import os

from unstructured_inference.logger import logger_onnx

from common.logger_setup import logger
from file_convert.config import COMMON_OUTPUT_PATH, SCHOOL_SIMPLE, ALL_FILES_PATH
import pypandoc

OUTPUT_PATH=COMMON_OUTPUT_PATH+SCHOOL_SIMPLE

def update_records(docx):
    with open(OUTPUT_PATH+"/config/records.txt",'a',encoding='utf-8') as f:
        f.write('\n'.join(docx))

def get_current_process():
    with open(OUTPUT_PATH+"/config/records.txt",'r',encoding='utf-8') as f:
        process = len(f.readlines())
    return process

# 有了主控制程序，这里能保证传过来的docx，是从未处理过的，也就是说，已经不用考虑重复的问题
def docx2md(docx,docx_cnt):
    try:
        finished_cnt = get_current_process()
        logger.info(f"正在转换docx:{docx},共有{docx_cnt}份docx,目前进度为{finished_cnt/docx_cnt}")
        # 获取文件名，给转换后的md文件命名
        base,ext = os.path.splitext(docx)
        # 将 .doc 文件转换为 .md
        md_output = pypandoc.convert_file(ALL_FILES_PATH+docx, 'markdown', outputfile=OUTPUT_PATH+'/'+ext+".md")

        update_records(docx)
    except Exception as e:
        logger.error(f"转换docx文件:{docx}失败")