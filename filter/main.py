import concurrent.futures
import json
import multiprocessing
import os

from tqdm import tqdm

from common.logger_setup import logger
from common.tools import get_current_datetime
from common.FileConvertProcessor import FileConvert
from filter.config import Filter_Config

FileConvert = FileConvert()
Config = Filter_Config()
OUTPUT_JSON_PATH:str=Config.PURIED_JSON_PATH+Config.SCHOOL_SIMPLE
LOCK = multiprocessing.Lock()

#TODO 可以独立出去的一个方法
def init()->(set,set,set):
    #检查目录是否存在，如果不存在就创建
    if not os.path.exists(OUTPUT_JSON_PATH):
        # 处理成功记录和失败记录配置文件
        os.makedirs(OUTPUT_JSON_PATH+"/config")
        file = open(OUTPUT_JSON_PATH+"/config/records.txt", 'w')
        file.close()

        empty_data={}
        with open(OUTPUT_JSON_PATH+"/config/logging_failed.json", 'w',encoding='utf-8') as f:
            json.dump(empty_data, f)

        # 根据Config指定的学校简写,从磁盘中读取对应的para_hash.txt
        file = open(OUTPUT_JSON_PATH+"/config/para_hash.txt",'w')
        file.close()
        #读取完毕
        return (set(),set(),set())
    else:
        finished_set = set()
        para_set = set()  #文段去重集合
        # 将所有已经处理过的文件的文件名以集合set形式装入内存
        with open(OUTPUT_JSON_PATH + "/config/records.txt", 'r', encoding='utf-8') as f:
            for line in f.readlines():
                finished_set.add(line.strip())
        with open(OUTPUT_JSON_PATH+"/config/logging_failed.json", 'r',encoding='utf-8') as f:
            failed_list = json.load(f)
        with open(OUTPUT_JSON_PATH+"/config/para_hash.txt",'r',encoding='utf-8') as f:
            for line in f.readlines():
                para_set.add(line.strip())
        #读取完毕
        return (finished_set, failed_list,para_set)

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

def data_filter(resources_queue,records,htmls_all_cnt,para_set:set[str]):
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
            FileConvert.convert(os.path.join(Config.RAW_HTML_PATH,raw_html),raw_html,para_set) # 转换并保存为json和md

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

def create_process(resources_queue,records,htmls_all_cnt,para_set:set[str]):
    for id in range(Config.MAXNUM_PROCESSES):
        process = multiprocessing.Process(name=f"进程{id}",target=data_filter,args=(resources_queue,records,htmls_all_cnt,para_set))
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
    records,fails,para_set = init()
    #实时计算records的大小size，这代表着进度->size/len(raw_htmls)
    htmls_all_finished = len(records)
    #实时计算logging_failed.json中失败或无效的文件数目
    htmls_all_failed = len(fails)

    logger.info("开始进行数据清洗...")
    logger.info(f"当前总任务数: {htmls_all_cnt},已完成的任务数:{htmls_all_finished},失败或无效的任务数:{htmls_all_failed}")
    pbar = tqdm(initial=htmls_all_finished,total=htmls_all_cnt)
    pbar.refresh()
    create_process(resources_queue, records,htmls_all_cnt,para_set)
    # 将其全都放入资源队列中
    for raw_html in raw_htmls:
        resources_queue.put(raw_html)

    resources_queue.join()
    logger.info(f"已完成数据清洗工作，一共处理得到{len(records)}份有效数据文件")

if __name__ == '__main__':
    main()