import json
import multiprocessing
import os

from tqdm import tqdm

from common.logger_setup import logger
from common.tools import scan_files, get_current_datetime
from file_convert.config import Convert_Config
from file_convert import FileConvert
from file_convert.docx2md.main import docx2md
from file_convert.pdf2md.main import pdf2md
from file_convert.tools.doc2docx import convert_doc_to_docx
from file_convert.tools.xls2xlsx import convert_xls_to_xlsx
from file_convert.xlsx2md.main import xlsx2md

FileConvert = FileConvert()
Config = Convert_Config()
LOCK = multiprocessing.Lock()
# Python-Working-Directory:[Project]\\file_convert
def init()->(set,set):
    records_set = set()
    fails_set = set()
    for work_dir in Convert_Config.WORK_DIRS:
        # 检查目录是否存在，如果不存在就创建
        work_path = Config.COMMON_OUTPUT_PATH+'/'+work_dir+Config.SCHOOL_SIMPLE+'/config'
        if not os.path.exists(work_path):
            os.makedirs(work_path)
            file = open(work_path+"/records.txt",'w')
            file.close()
            empty_data={}
            with open(work_path+"/logging_failed.json",'w',encoding='utf8') as f:
                json.dump(empty_data,f)
        else:
            with open(work_path+"/records.txt",'r',encoding='utf-8') as f:
                for line in f.readlines():
                    records_set.add(line.strip())
            with open(work_path+"/logging_failed.json",'r',encoding='utf-8') as f:
                fails_set = json.load(f)
    return (records_set,fails_set)

def logging_failed(file_name:str):
    file_path = 'logging_failed.json'
    cur_time = get_current_datetime()
    with open(file_path,'r',encoding='utf-8') as f:
        data:dict = json.load(f)
    data[file_name]=cur_time
    with open(file_path,'w',encoding='utf-8') as f:
        json.dump(data,f,indent=4,ensure_ascii=False)

def __doc2md(doc_name,docx_cnt):
    doc_path = Config.ALL_FILES_PATH+doc_name
    docx_path = doc_path+'x'
    docx_name = doc_name+'x'
    convert_doc_to_docx(doc_path,docx_path)
    docx2md(docx_name,docx_cnt)

def __xls2md(xls_name,xlsx_cnt):
    xls_path = Config.ALL_FILES_PATH+xls_name
    xlsx_path = xls_path+'x'
    xlsx_name = xls_name+'x'
    convert_xls_to_xlsx(xls_path,xlsx_path)
    xlsx2md(xlsx_name,xlsx_cnt)

# TODO 主控制程序和日志记录程序写在这里，失败和成功信息记录就写在各转换目录下
# 这是主控制程序，宏观来看，主要追踪当前正在处理哪些文件，目前总任务的进度在哪里
def server_distribute(files_queue,ext_dict,records,fails:int,all_cnt_tasks):
    pbar = tqdm(initial=len(records),total=all_cnt_tasks)
    while True:
        file_name:str = files_queue.get()
        try:
            if file_name in records or file_name+"x" in records: # TODO 查重异常
                continue
            logger.info(f"当前正在转换文件:{file_name}")
            if file_name.endswith(".pdf"):
                pdf2md(file_name)
            else:
                md_content = FileConvert.read(Convert_Config.ALL_FILES_PATH.join(file_name)) # 对pdf使用原有的MinerU来实现
                base,ext = os.path.splitext(file_name)
                with open(Config.COMMON_OUTPUT_PATH+'/'+base+".md",'w',encoding="utf-8") as f:
                    f.write(md_content)
            records.add(file_name)
            # 更新进度条
            pbar.update(1)
        except Exception as e:
            # 记录失败次数
            with LOCK:
                logger.error(f"文件:{file_name}转换失败,失败原因为:{e}")
        finally:
            files_queue.task_done()

def create_processes(files_queue,ext_dict,records,fails,all_cnt_tasks):
    for id in range(Config.MAXNUM_PROCESSES):
        process = multiprocessing.Process(name=f"进程{id}",target=server_distribute,args=(files_queue,ext_dict,records,fails,all_cnt_tasks))
        process.daemon = True
        process.start()

def main():
    files_queue = multiprocessing.JoinableQueue()
    name_of_files = os.listdir(Config.ALL_FILES_PATH)
    # 指定路径下的pdf,docx,xlsx有多少个
    ext_dict = scan_files(Config.ALL_FILES_PATH,Config.CONVERT_EXTENSIONS)
    all_cnt_tasks = sum(ext_dict.values())
    # 转换成功/失败的总数
    records,fails = init()
    logger.info("开始进行文档转换...")
    logger.info(f"当前总任务数:{all_cnt_tasks},已完成的任务数:{len(records)},转换失败的任务数:{len(fails)}")
    pbar = tqdm(initial=len(records),total=all_cnt_tasks)
    pbar.refresh()
    create_processes(files_queue,ext_dict,records,fails,all_cnt_tasks)

    # 文件都放入资源队列中
    for file in name_of_files:
        files_queue.put(file)

    files_queue.join()
    logger.info(f'已完成文档转换工作，一共处理得到{len(files_queue)}份MD文档')

if __name__ == '__main__':
    main()