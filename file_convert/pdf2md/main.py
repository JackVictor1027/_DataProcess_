import os
import subprocess
import re
import requests

from common.logger_setup import logger
from file_convert.config import Convert_Config

Config = Convert_Config()
# pdf的解析较为复杂，使用MinerU效果最好
OUTPUT_PATH:str = Config.COMMON_OUTPUT_PATH+"pdf2md/"+Config.SCHOOL_SIMPLE  # E:\Output\x2md\pdf2md\...\1553243419369070956\auto

def update_records(pdf):
    with open(OUTPUT_PATH+"/config/records.txt",'a',encoding='utf-8') as f:
        f.write(pdf+"\n")

def get_current_process():
    with open(OUTPUT_PATH+"/config/records.txt",'r',encoding='utf-8') as f:
        process = len(f.readlines())
    return process

def pdf2md(pdf_file):
    try:
        logger.info(f"正在转换pdf:{pdf_file}")
        # 调用批处理脚本
        subprocess.run(["magic-pdf","-p",Config.ALL_FILES_PATH+pdf_file,"-o",OUTPUT_PATH])
        #更新记录表
        update_records(pdf_file)
    except Exception as e:
        logger.error(f"转换pdf文件:{pdf_file}失败")
        raise # 将异常传递给调用方

def test_pdf2md():
    pdf2md("1714353255884023804.pdf",10)