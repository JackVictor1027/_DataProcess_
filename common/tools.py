import hashlib
import json
import re,jieba
from datetime import datetime
import os
from os.path import isfile

import jieba.analyse
from sympy.codegen.fnodes import intent_inout

from filter.config import Filter_Config
from file_convert.config import Convert_Config

fc = Filter_Config()
cc = Convert_Config()
OUTPUT_JSON_PATH=fc.PURIED_JSON_PATH+fc.SCHOOL_SIMPLE

#将work_path路径下，指定学校的所有处理后文件和记录全部删除，回到任务的初始状态
# ../file_convert/xlsx2md/   hbfu
def restart(work_path,school):
    work_path = work_path+school
    files = os.listdir(work_path)
    for file in files:
        if os.path.isfile(work_path+"/"+file):
            os.remove(work_path+"/"+file)

    # 清空logging_failed.json和records.txt
    with open(work_path+"/config/records.txt","w",encoding="utf-8") as f:
        f.write("")
    with open(work_path+"/config/logging_failed.json","w",encoding="utf-8") as f:
        f.write("{}")

def generate_hash_value(content:str) -> str:
    """ 计算仅和内容有关的稳定哈希值 """
    hash_value_content = hashlib.sha256()
    # 处理成字符串
    hash_value_content.update(content.encode('utf-8'))
    # 返回哈希值
    return hash_value_content.hexdigest()

def extract_keywords(content:str)->str:
    content = re.sub(r'<[^>]+>', '', content).strip()
    tags = jieba.analyse.extract_tags(sentence=content, topK=fc.TOP_K)

    return str(tags)

def get_current_datetime():
    now_time = datetime.now()
    current_time = now_time.strftime("%Y-%m-%d %H:%M:%S")
    return current_time

def save_as_json(title:str,publish_date:str,keywords:str,category:str,md_content:str,hashValue:str) -> None:
    json_content = {
        "school_id": fc.SCHOOL_ID,
        "school_name": fc.SCHOOL_NAME,
        "title": title,
        "create_at": get_current_datetime(),
        "publish_date": publish_date,
        "keywords": keywords,
        "category": category,
        "content": md_content,
        "hashValue": hashValue,
    }
    try:
        with open(OUTPUT_JSON_PATH + "/"+title + ".json", "w", encoding='utf-8') as f:
            # f.write(json_content)
            json.dump(json_content, f, indent=4, ensure_ascii=False)
    except Exception as e:
        #TODO 异常处理
        pass

def scan_files(dir,extensions)->dict:
    """
    扫描指定目录下的文件，并返回所有指定文件类型的对应数目。
    :param dir: 要扫描的目录路径
    :param extensions: 文件后缀名列表，如['.docx','.pdf']
    :return:
    """
    file_names = os.listdir(dir)
    ext_dict={}
    for file_name in file_names:
        ext = os.path.splitext(file_name)[1]
        if ext in extensions:
            if ext_dict.get(ext) is not None:
                ext_dict[ext]+=1
            else:
                ext_dict[ext]=1
    return ext_dict

def test_scan_files():
    path = "D:/TechDream/AI/AI_LLM_query/data/hbfu/files/lib.hbfu.edu.cn"
    d = scan_files(path,cc.CONVERT_EXTENSIONS)
    print(d)

def test_restart():
    work_path = "../file_convert/pdf2md/"
    school = fc.SCHOOL_SIMPLE
    restart(work_path,school)