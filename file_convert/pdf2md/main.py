import os
import subprocess

from fontTools.unicodedata import script
os.chdir(os.getcwd()+"\\pdf2md\\")
from common.logger_setup import logger
from file_convert.config import COMMON_OUTPUT_PATH, SCHOOL_SIMPLE, ALL_FILES_PATH

# pdf的解析较为复杂，使用MinerU效果最好
OUTPUT_PATH = SCHOOL_SIMPLE

def update_records(pdf):
    with open(OUTPUT_PATH+"/config/records.txt",'a',encoding='utf-8') as f:
        f.write(pdf)

def get_current_process():
    with open(OUTPUT_PATH+"/config/records.txt",'r',encoding='utf-8') as f:
        process = len(f.readlines())
    return process

def pdf2md(pdf_file,pdf_cnt):
    try:
        finished_cnt = get_current_process()
        logger.info(f"正在转换pdf:{pdf_file},共有{pdf_cnt}份pdfk,目前进度为{finished_cnt/pdf_cnt}")
        # 调用批处理脚本
        subprocess.run(["magic-pdf","-p",ALL_FILES_PATH+pdf_file,"-o","hbfu/"])

        #更新记录表
        update_records(pdf_file)
    except Exception as e:
        logger.error(f"转换pdf文件:{pdf_file}失败")

def test_pdf2md():
    pdf2md("1714353255884023804.pdf",10)