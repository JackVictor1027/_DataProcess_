import hashlib
import json
import re,jieba
from datetime import datetime

import jieba.analyse
from filter.config import TOP_K, SCHOOL_ID, SCHOOL_NAME, PURIED_JSON_PATH, SCHOOL_SIMPLE

OUTPUT_JSON_PATH=PURIED_JSON_PATH+SCHOOL_SIMPLE

def generate_hash_value(content:str) -> str:
    """ 计算仅和内容有关的稳定哈希值 """
    hash_value_content = hashlib.sha256()
    # 处理成字符串
    hash_value_content.update(content.encode('utf-8'))
    # 返回哈希值
    return hash_value_content.hexdigest()

def extract_keywords(content:str)->str:
    content = re.sub(r'<[^>]+>', '', content).strip()
    tags = jieba.analyse.extract_tags(sentence=content, topK=TOP_K)

    return str(tags)

def get_current_datetime():
    now_time = datetime.now()
    current_time = now_time.strftime("%Y-%m-%d %H:%M:%S")
    return current_time

def save_as_json(title:str,publish_date:str,keywords:str,category:str,md_content:str,hashValue:str) -> None:
    json_content = {
        "school_id": SCHOOL_ID,
        "school_name": SCHOOL_NAME,
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