import concurrent.futures
import json
import logging
import os
import bs4
import re
from bs4 import Comment, element
from tqdm import tqdm
import common
from common.local_models import query_for_local_model
from common.tools import generate_hash_value, extract_keywords, save_as_json, get_current_datetime
from file_convert.tools.html2md_custom_markdown import html2md
from filter.config import Filter_Config
import markdown
from common.logger_setup import logger
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from multiprocessing import Queue,Process,Lock

Config = Filter_Config()
OUTPUT_JSON_PATH=Config.PURIED_JSON_PATH+Config.SCHOOL_SIMPLE
LOCK = multiprocessing.Lock()

#TODO 可以独立出去的一个方法
def init()->(set,set):
    #检查目录是否存在，如果不存在就创建
    if not os.path.exists(OUTPUT_JSON_PATH):
        # 处理成功记录和失败记录配置文件
        os.makedirs(OUTPUT_JSON_PATH+"/config")
        file = open(OUTPUT_JSON_PATH+"/config/records.txt", 'w')
        file.close()
        empty_data={}
        with open(OUTPUT_JSON_PATH+"/config/logging_failed.json", 'w',encoding='utf-8') as f:
            json.dump(empty_data, f)
        return (set(),set())
    else:
        finished_set = set()
        # 将所有已经处理过的文件的文件名以集合set形式装入内存
        with open(OUTPUT_JSON_PATH + "/config/records.txt", 'r', encoding='utf-8') as f:
            for line in f.readlines():
                finished_set.add(line.strip())
        with open(OUTPUT_JSON_PATH+"/config/logging_failed.json", 'r',encoding='utf-8') as f:
            failed_list = json.load(f)
        return (finished_set, failed_list)

def update_records(finished_html):
    file_path = OUTPUT_JSON_PATH + "/config/records.txt"
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(finished_html+"\n")

def logging_failed(file_name:str):
    file_path = OUTPUT_JSON_PATH+"/config/logging_failed.json"
    cur_time = get_current_datetime()
    with open(file_path,'r',encoding='utf-8') as f:
        data:dict = json.load(f)
    data[file_name]=cur_time
    with open(file_path,'w',encoding='utf-8') as f:
        json.dump(data,f,indent=4,ensure_ascii=False)

def generate_attrs(content)->dict:
    data = {
        "model":Config.LOCAL_MODEL,
        "prompt":
            Config.PROMPT_OF_ATTRS+content,
        "stream":False
    }
    attrs = query_for_local_model(data)
    response = json.loads(attrs.text)['response']
    attrs = json.loads(response)
    return attrs

def replace_images_with_local_urls(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        def replacement(match):
            original_url = match.group(1)
            # 下载图片并获取新的本地路径
            local_url = save_image(original_url)
            if local_url:
                # 构造新的图片标签
                new_tag = f'![{match.group(0)[2:]}({local_url})'
                return new_tag
            else:
                # 如果上传失败，保留原始标签
                return match.group(0)

        new_content = image_pattern.sub(replacement, content)

        # 将新内容写回原文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"成功替换了文件 {file_path} 中的所有图片标签。")

    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
    except Exception as e:
        print(f"处理文件时发生错误: {e}")

def handle_wash(html:str):
    head, ext = os.path.splitext(file_name)
    md_content = html2md(html_content)
    # 正则表达式匹配多个换行符，用一个换行符全替换
    pat = r'\n{2,}'
    md_content = re.sub(pat, '\n', md_content)
    replace_images_with_local_urls()

def first_filter(html:str)->str:
    """
    第一步清洗：
        下载当前页面所有图片至本地
        链接、JS代码段、注释、指定标签
    """
    try:
        soup = bs4.BeautifulSoup(html,"html.parser")

        # 删去所有的<script> <style>标签与内部内容
        for s in soup(["script", "style"]):
            s.extract()

        # 常见的样式标签
        multiform_tags = ['iframe', 'textarea','metadata'] #TODO:考虑保留图片
        for tag in multiform_tags:
            for element in soup.find_all(tag):
                element.extract()

        # 删去所有的注释文本
        comments = soup.findAll(string = lambda text:isinstance(text, Comment))
        for comment in comments:
            comment.extract()
    except Exception as e:
        #TODO 异常处理
        return "None"
    return soup.prettify()

def second_wash(html:str)->str:
    """
        第二步清洗：模糊匹配页眉页脚，去除所有内嵌样式，通过枚举筛去带有id,class属性的标签
    """
    try:
        # 枚举删去繁琐的css样式
        soup = bs4.BeautifulSoup(html,"html.parser")
        tags = Config.ID_AND_CLASS_TAGS
        for tag in tags:
            [element.extract() for element in soup.find_all(class_=tag)]
            [element.extract() for element in soup.find_all(id=tag)]
        #模糊匹配
        tags= Config.FUZZY_TAGS
        for tag in tags:
            [element.extract() for element in soup.find_all(class_=re.compile(tag))]
            [element.extract() for element in soup.find_all(id=re.compile(tag))]
        # 删去所有的标签属性
        for tag in soup.find_all(True):
            tag.attrs = {}
    except Exception as e:
        return "None"
    return soup.prettify()

def third_process(html:str)->str:
    """
        第三步处理：使用markdownify库(不借助大模型效率更高)，将html转为md，过程中解析表格
        接着，我们开始按照指定的格式为每一篇文章，构建相应的JSON
        最后，使用上一步中本地大模型生成的标题对其命名后，保存为json最终文件。
        为了日志记录，我们需要返回文章标题
    """
    md_content = html2md(html)
    # 正则表达式匹配多个换行符，用一个换行符全替换
    pat = r'\n{2,}'
    md_content = re.sub(pat,'\n',md_content)
    hash_value = generate_hash_value(md_content)
    keywords = extract_keywords(markdown.markdown(html)) #TODO:冗余操作？

    """
        第四步-大模型
    """
    attrs = generate_attrs(md_content)
    save_as_json(attrs["title"],attrs["publish_date"],keywords,attrs["category"],md_content,hash_value)
    return attrs['title']

def data_filter(resources_queue,records,htmls_all_cnt):
    # 设置进度条
    # 主循环
    pbar = tqdm(initial=len(records), total=htmls_all_cnt)
    while True:
        raw_html = resources_queue.get()
        try:
            # 已经是处理过的文件了，直接跳过
            if raw_html in records:
                continue
            with LOCK:
                logger.info(f"{multiprocessing.current_process().name}当前正在对文件:{raw_html}进行清洗工作")
            with open(os.path.join(Config.RAW_HTML_PATH,raw_html),'r',encoding='utf-8') as f:
                raw_content = f.read()
            _html1 = first_filter(raw_content) #第一步清洗
            _html2 = second_wash(_html1) #第二步清洗
            third_process(_html2) #第三步处理并对文本重排进行格式化,得到最终的纯净MD

            with LOCK:
                records.add(raw_html)
                update_records(raw_html)#写入记录表
                #更新进度条
                pbar.update(1)
        except Exception as e:
            #记录错误记录
            with LOCK:
                logger.error(f"线程{multiprocessing.current_process().name}清洗文件{raw_html}失败,原因:{e}")
                logging_failed(raw_html)
        finally:
            resources_queue.task_done()

def create_process(resources_queue,records,htmls_all_cnt):
    for id in range(Config.MAXNUM_PROCESSES):
        process = multiprocessing.Process(name=f"进程{id}",target=data_filter,args=(resources_queue,records,htmls_all_cnt))
        process.daemon = True # 守护进程
        process.start()

def create_process_pool(resources_queue,records,htmls_all_cnt):
    futures = set()
    with concurrent.futures.ProcessPoolExecutor(max_workers=Config.MAXNUM_PROCESSES) as executor:
        for i in range(Config.MAXNUM_PROCESSES):
            future = executor.submit(data_filter,resources_queue,records,htmls_all_cnt)
            futures.add(future)
        for future in concurrent.futures.as_completed(futures):
            err = future.exception()
            if err is None:
                result = future.result()
            else:
                logger.error(f"future对象处理文件失败,原因为:{err}")

def main():
    #从路径中获取所有HTML文档的文件名
    raw_htmls = os.listdir(Config.RAW_HTML_PATH)
    # 统计所有的文件个数
    htmls_all_cnt = len(raw_htmls)
    resources_queue = multiprocessing.JoinableQueue()  # 资源队列
    # 读取已完成/失败的记录表 records(set)
    records,fails = init()
    #实时计算records的大小size，这代表着进度->size/len(raw_htmls)
    htmls_all_finished = len(records)
    #实时计算logging_failed.json中失败或无效的文件数目
    htmls_all_failed = len(fails)

    logger.info("开始进行数据清洗...")
    logger.info(f"当前总任务数: {htmls_all_cnt},已完成的任务数:{htmls_all_finished},失败或无效的任务数:{htmls_all_failed}")
    pbar = tqdm(initial=htmls_all_finished,total=htmls_all_cnt)
    pbar.refresh()
    create_process(resources_queue, records,htmls_all_cnt)
    # 将其全都放入资源队列中
    for raw_html in raw_htmls:
        resources_queue.put(raw_html)

    resources_queue.join()
    logger.info(f"已完成数据清洗工作，一共处理得到{len(records)}份有效数据文件")

if __name__ == '__main__':
    main()