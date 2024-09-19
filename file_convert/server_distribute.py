import json
import os
import queue
import threading

from litellm.proxy.proxy_server import queue
from sympy.strategies.core import switch
from tensorboard.compat.tensorflow_stub.dtypes import resource
from tqdm import tqdm

from common.logger_setup import logger
from common.tools import scan_files, get_current_datetime
from file_convert.config import ALL_FILES_PATH, WORK_DIRS, NUM_THREADS
from file_convert.docx2md.main import docx2md
from file_convert.pdf2md.main import pdf2md
from file_convert.tools.doc2docx import convert_doc_to_docx
from file_convert.tools.xls2xlsx import convert_xls_to_xlsx
from file_convert.xlsx2md.main import xlsx2md
from file_convert.config import CONVERT_EXTENSIONS, SCHOOL_SIMPLE

# Python-Working-Directory:[Project]\\file_convert

def get_resource_queue(name_of_files:list[str])->queue.Queue:
    que = queue.Queue()
    for resource in name_of_files:
        que.put(resource)

def init()->(set,set):
    records_set = set()
    fails_set = set()
    for work_dir in WORK_DIRS:
        # 检查目录是否存在，如果不存在就创建
        work_path = work_dir+SCHOOL_SIMPLE+'/config'
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
    doc_path = ALL_FILES_PATH+doc_name
    docx_path = doc_path+'x'
    docx_name = doc_name+'x'
    convert_doc_to_docx(doc_path,docx_path)
    docx2md(docx_name,docx_cnt)

def __xls2md(xls_name,xlsx_cnt):
    xls_path = ALL_FILES_PATH+xls_name
    xlsx_path = xls_path+'x'
    xlsx_name = xls_name+'x'
    convert_xls_to_xlsx(xls_path,xlsx_path)
    xlsx2md(xlsx_name,xlsx_cnt)

# 主控制程序和日志记录程序写在这里，失败和成功信息记录就写在各转换目录下
# 这是主控制程序，宏观来看，主要追踪当前正在处理哪些文件，目前总任务的进度在哪里
def server_distribute():
    name_of_files = os.listdir(ALL_FILES_PATH) #获取所有文件的文件名
    que_of_resources = get_resource_queue(name_of_files) # 资源队列
    # 指定路径下的pdf,docx,xlsx有多少个
    ext_dict = scan_files(ALL_FILES_PATH,CONVERT_EXTENSIONS)
    all_cnt_tasks = sum(ext_dict.values())
    # 转换成功/失败的总数
    records,fails = init()
    logger.info("开始进行文档转换...")
    logger.info(f"当前总任务数:{all_cnt_tasks},已完成的任务数:{len(records)},转换失败的任务数:{len(fails)}")
    with tqdm(total=all_cnt_tasks) as pbar:
        pbar.n = records
        for file_name in name_of_files and not que_of_resources.empty():
            try:
                if file_name in records or file_name+"x" in name_of_files: # TODO 查重异常
                    continue
                file_name = que_of_resources.get_nowait() # 从队列中取出资源，使用get_nowait()是为了防止程序卡住
                logger.info(f"当前正在转换文件:{file_name}")
                #获取文件后缀名，分配对应的服务
                base,ext = os.path.splitext(file_name)
                match ext:
                    case ".pdf":pdf2md(file_name,ext_dict['.pdf'])
                    case ".doc":
                         __doc2md(file_name, ext_dict['.docx'] + ext_dict['.doc'])
                    case ".docx":
                         docx2md(file_name, ext_dict['.docx'] + ext_dict['.doc'])
                    case ".xls":
                         __xls2md(file_name, ext_dict['.xlsx'] + ext_dict['.xls'])
                    case ".xlsx":
                         xlsx2md(file_name, ext_dict['.xlsx'] + ext_dict['.xlsx'])
                    case _:
                        logger.info(f"转换失败,此文件类型暂不支持转换:{file_name}")
                        fails += 1
                        continue

                records.add(file_name)
            except queue.Empty:
                pass
            except Exception as e:
                # 记录失败次数
                logger.error(f"文件:{file_name}转换失败,失败原因:{e}")
                fails+=1
            # 更新进度条
            pbar.n = len(records)
            pbar.refresh()
    logger.info(f'已完成文档转换工作，一共处理得到{records}份MD文档')


if __name__ == '__main__':
    threads = []
    for i in range(NUM_THREADS): # 创建NUM个线程
        t = threading.Thread(target=server_distribute,args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()