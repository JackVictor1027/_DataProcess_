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

def upload_image_to_server(image_url):
    # 从原始URL下载图片
    response = requests.get(image_url)
    if response.status_code != 200:
        print(f"无法下载图片: {image_url}")
        return None

    # 将图片以二进制形式发送到服务器
    server_response = requests.post('http://localhost:5000/img', files={'file': response.content})
    if server_response.status_code == 200:
        # 假设服务器返回的是一个JSON对象，其中包含新的URL
        new_url = server_response.json().get('url')
        if new_url:
            return new_url
        else:
            print("服务器未返回有效的URL")
    else:
        print(f"服务器返回错误状态码: {server_response.status_code}")
    return None

def replace_images_with_remote_urls(file_path):
    # 定义匹配Markdown图片的正则表达式
    image_pattern = re.compile(r'!\[.*?\]\((.*?)\)')

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        def replacement(match):
            original_url = match.group(1)
            # 上传图片并获取新的远程URL
            remote_url = upload_image_to_server(original_url)
            if remote_url:
                # 构造新的图片标签
                new_tag = f'![{match.group(0)[2:]}({remote_url})'
                return new_tag
            else:
                # 如果上传失败，保留原始标签
                return match.group(0)

        new_content = image_pattern.sub(replacement, content)

        # 将新内容写回原文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"成功替换了文件 {file_path} 中的所有图片标签。")

    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
    except Exception as e:
        print(f"处理文件时发生错误: {e}")


def pdf2md(pdf_file,pdf_cnt):
    try:
        finished_cnt = get_current_process()
        logger.info(f"正在转换pdf:{pdf_file},共有{pdf_cnt}份pdf,目前进度为{finished_cnt/pdf_cnt}")
        # 调用批处理脚本
        subprocess.run(["magic-pdf","-p",Config.ALL_FILES_PATH+pdf_file,"-o",OUTPUT_PATH])
        pdf_name,_ = os.path.splitext(pdf_file)
        md_path_converted = os.path.join(OUTPUT_PATH,pdf_name,"auto",pdf_name+".md")
        # 更换图片连接为远程
        replace_images_with_remote_urls(md_path_converted)
        #更新记录表
        update_records(pdf_file)
    except Exception as e:
        logger.error(f"转换pdf文件:{pdf_file}失败")
        raise # 将异常传递给调用方

def test_pdf2md():
    pdf2md("1714353255884023804.pdf",10)