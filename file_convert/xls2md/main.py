import os
import pandas as pd
from tabulate import tabulate
from unstructured_inference.logger import logger_onnx

from common.logger_setup import logger
from file_convert.config import COMMON_OUTPUT_PATH, SCHOOL_SIMPLE, ALL_FILES_PATH
import pypandoc

OUTPUT_PATH=COMMON_OUTPUT_PATH+SCHOOL_SIMPLE

def update_records(xlsx):
    with open(OUTPUT_PATH+"/config/records.txt",'a',encoding='utf-8') as f:
        f.write('\n'.join(xlsx))

def get_current_process():
    with open(OUTPUT_PATH+"/config/records.txt",'r',encoding='utf-8') as f:
        process = len(f.readlines())
    return process

# 有了主控制程序，这里能保证传过来的xlsx，是从未处理过的，也就是说，已经不用考虑重复的问题
def xlsx2md(xlsx,xlsx_cnt):
    try:
        finished_cnt = get_current_process()
        logger.info(f"正在转换xlsx:{xlsx},共有{xlsx_cnt}份xlsx,目前进度为{finished_cnt/xlsx_cnt}")
        # 获取文件名，给转换后的md文件命名
        base,ext = os.path.splitext(xlsx)
        # 使用panda读取Excel文件
        df = pd.read_excel(ALL_FILES_PATH+xlsx)

        # panda解析，将空白单元格填充为“无数据”
        df.fillna('无数据', inplace=True)

        # headers='keys'表示第一行作为表头，pipe模式的作用是使结果以markdown表格格式输出
        md_table = tabulate(df, headers='keys', tablefmt='pipe')

        # 存储到文件
        with open(OUTPUT_PATH+'/'+base+'.md', 'w', encoding='utf-8') as f:
            f.write(md_table)

        update_records(xlsx)
    except Exception as e:
        logger.error(f"转换xlsx文件:{xlsx}失败")