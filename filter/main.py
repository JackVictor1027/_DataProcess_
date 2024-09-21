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
from filter.config import RAW_HTML_PATH, ID_AND_CLASS_TAGS, FUZZY_TAGS, LOCAL_MODEL, PROMPT_OF_ATTRS, PURIED_JSON_PATH, \
    SCHOOL_SIMPLE, MAXNUM_PROCESSES
import markdown
from common.logger_setup import logger
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from multiprocessing import Queue,Process,Lock

OUTPUT_JSON_PATH=PURIED_JSON_PATH+SCHOOL_SIMPLE
resources_queue = multiprocessing.Queue()
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
        "model":LOCAL_MODEL,
        "prompt":
            PROMPT_OF_ATTRS+content,
        "stream":False
    }
    attrs = query_for_local_model(data)
    response = json.loads(attrs.text)['response']
    attrs = json.loads(response)
    return attrs

def first_filter(html:str)->str:
    """
    第一步清洗：链接、图片、JS代码段、注释、指定标签
    """
    try:
        soup = bs4.BeautifulSoup(html,"html.parser")

        # 删去所有的<script> <style>标签与内部内容
        for s in soup(["script", "style"]):
            s.extract()

        # 常见的样式标签
        multiform_tags = ['img', 'iframe', 'textarea','metadata'] #TODO:考虑保留图片
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
        tags = ID_AND_CLASS_TAGS
        for tag in tags:
            [element.extract() for element in soup.find_all(class_=tag)]
            [element.extract() for element in soup.find_all(id=tag)]
        #模糊匹配
        tags= FUZZY_TAGS
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

def data_filter(raw_html,records:set[str])->bool:
    # 设置进度条
    # TODO 进度条不适合放在线程运行中
    # 主循环
    try:
        # 已经是处理过的文件了，直接跳过
        if raw_html in records:
            return False
        logger.info(f"线程{multiprocessing.current_process().name}当前正在对文件:{raw_html}进行清洗工作")
        with open(os.path.join(RAW_HTML_PATH,raw_html),'r',encoding='utf-8') as f:
            raw_content = f.read()
        _html1 = first_filter(raw_content) #第一步清洗
        _html2 = second_wash(_html1) #第二步清洗
        third_process(_html2) #第三步处理并对文本重排进行格式化,得到最终的纯净MD

        records.add(raw_html)
        update_records(raw_html)#写入记录表
        return True
    except Exception as e:
        #记录错误记录
        logger.error(f"线程{multiprocessing.current_process().name}清洗文件{raw_html}失败,原因:{e}")
        logging_failed(raw_html)
        return False

async def async_woker(records:set[str]):
    while not resources_queue.empty():
        raw_html = resources_queue.get()
        state = await data_filter(raw_html,records)
        sleep

def run_worker(records:set[str]):
    Process.run(async_woker,records)

if __name__ == '__main__':
    #从路径中获取所有HTML文档的文件名
    raw_htmls = os.listdir(RAW_HTML_PATH)
    # 将其全都放入资源队列中
    for raw_html in raw_htmls:
        resources_queue.put(raw_html)
    # 统计所有的文件个数
    htmls_all_cnt = len(raw_htmls)
    #读取已完成/失败的记录表 records(set)
    records,fails = init()
    #实时计算records的大小size，这代表着进度->size/len(raw_htmls)
    htmls_all_finished = len(records)
    #实时计算logging_failed.json中失败或无效的文件数目
    htmls_all_failed = len(fails)

    logger.info("开始进行数据清洗...")
    logger.info(f"当前总任务数: {htmls_all_cnt},已完成的任务数:{htmls_all_finished},失败或无效的任务数:{htmls_all_failed}")

    with tqdm(total=htmls_all_cnt) as pbar:
        with concurrent.futures.ThreadPoolExecutor(MAXNUM_PROCESSES) as executor:
            tasks = [executor.submit(data_filter,raw_htmls,htmls_all_cnt,records,htmls_all_failed) for _ in range(MAXNUM_PROCESSES)]
            for task in concurrent.futures.as_completed(tasks):
                task.result()
            pbar.n = len(records)
            pbar.refresh()

    logger.info(f"已完成数据清洗工作，一共处理得到{htmls_all_finished}份有效数据文件")
