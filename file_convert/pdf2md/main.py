import os
import subprocess

from fontTools.unicodedata import script
from numpy.f2py.auxfuncs import throw_error

from common.logger_setup import logger
from file_convert.config import COMMON_OUTPUT_PATH, SCHOOL_SIMPLE, ALL_FILES_PATH

# pdf的解析较为复杂，使用MinerU效果最好
OUTPUT_PATH = "./pdf2md/"+SCHOOL_SIMPLE

def update_records(pdf):
    with open(OUTPUT_PATH+"/config/records.txt",'a',encoding='utf-8') as f:
        f.write(pdf+"\n")

def get_current_process():
    with open(OUTPUT_PATH+"/config/records.txt",'r',encoding='utf-8') as f:
        process = len(f.readlines())
    return process

def pdf2md(pdf_file,pdf_cnt):
    try:
        finished_cnt = get_current_process()
        logger.info(f"正在转换pdf:{pdf_file},共有{pdf_cnt}份pdf,目前进度为{finished_cnt/pdf_cnt}")
        # 调用批处理脚本
        # subprocess.run(["magic-pdf","-p",ALL_FILES_PATH+pdf_file,"-o",OUTPUT_PATH])

        #更新记录表
        update_records(pdf_file)
    except Exception as e:
        logger.error(f"转换pdf文件:{pdf_file}失败")
        raise # 将异常传递给调用方

def test_pdf2md():
    pdf2md("1714353255884023804.pdf",10)