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
from common.tools import generate_hash_value, extract_keywords, save_as_json, get_current_datetime, recover_url_of_img, \
    save_as_md
from file_convert.tools.html2md_custom_markdown import html2md
from filter.config import Filter_Config
import markdown
from common.logger_setup import logger
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from file_convert.file_convert import FileConvert
from multiprocessing import Queue,Process,Lock

FileConvert = FileConvert()
Config = Filter_Config()
OUTPUT_JSON_PATH:str=Config.PURIED_JSON_PATH+Config.SCHOOL_SIMPLE
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
    attrs = json.loads(response) # TODO bug
    return attrs

def get_html_link(html_name:str)->str:
    with open("html_urls_mapping.json","r") as f:
        url_table = json.loads(f.read())
    return url_table[html_name]

def replace_images_with_local_urls(content,attrs,html_name)->str:
    def replacement(match):
        original_url:str = match.group(1)
        # 解析标签
        if original_url.startswith("http") or original_url.startswith("https"):
            # 下载图片并获取新的本地路径
            local_url = FileConvert.save_image(original_url, os.path.join(OUTPUT_JSON_PATH, attrs["title"]))
        else:
            # 通过查询映射表，还原得到原html链接
            # TODO bug
            compl_list = original_url.split(" ")
            original_url = compl_list[0]
            html_link = get_html_link(html_name)
            img_url = recover_url_of_img(html_link,original_url)
            local_url = FileConvert.save_image(img_url, os.path.join(OUTPUT_JSON_PATH, attrs["title"]))
        if local_url:
            # 构造新的图片标签
            new_tag = f'![{local_url[0]}]({local_url[1]})'
            return new_tag
        else:
            # 如果上传失败，保留原始标签
            return match.group(0)
    new_content = FileConvert.md_image_pattern.sub(replacement, content) # 调用replacement函数，并将content作为参数传递过去
    return new_content

def auto_wash(html_content:str):
    """
        使用markdownify库(不借助大模型效率更高)，将html转为md，过程中解析表格
    :param html_content:
    :return:
    """
    md_content = html2md(html_content)
    # 正则表达式匹配多个换行符，用一个换行符全替换
    pat = r'\n{2,}'
    md_content = re.sub(pat, '\n', md_content)

    return md_content

def attr_process(content:str,html_name)->str:
    """
        使用markdownify库(不借助大模型效率更高)，将html转为md，过程中解析表格
        接着，我们开始按照指定的格式为每一篇文章，构建相应的JSON
        最后，使用上一步中本地大模型生成的标题对其命名后，保存为json最终文件。
        为了日志记录，我们需要返回文章标题
    """
    hash_value = generate_hash_value(content)
    keywords = extract_keywords(content)
    attrs = generate_attrs(content)
    # 下载图片
    content = replace_images_with_local_urls(content,attrs,html_name)
    # 保存到每个md子节目，md与json是平级的，img都在下一级
    save_as_json(attrs["title"],attrs["publish_date"],keywords,attrs["category"],content,hash_value)
    save_as_md(attrs["title"],content)

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
            md_content = auto_wash(raw_content)
            attr_process(md_content,raw_html) #第三步处理并对文本重排进行格式化,得到最终的纯净MD

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