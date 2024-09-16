# 测试用文件

# from file_convert.tools.convert_custom_markdown import html2md
# import re
# with open("1.html","r",encoding="utf-8") as f:
#     html = f.read()
# md = html2md(html)
# # 正则表达式匹配多个换行符
# pattern = r'\n{2,}'
#
# # 使用一个换行符替换所有匹配的多个换行符
# modified_text = re.sub(pattern, '\n', md)
# print(modified_text)
#
# with open("1.md","w",encoding="utf-8") as f:
#     f.write(modified_text)
# import re
# import sys
#
# from markdown import markdown
# import jieba
# import jieba.analyse
#
# file_name="1.md"
# content = open(file_name,"r",encoding="utf-8").read()
# content = markdown(content) #转为html
# content = re.sub(r'<[^>]+>','',content).strip()
# tags = jieba.analyse.extract_tags(sentence=content,topK=10)
# temp = str(tags)
# print(temp)
import json
from urllib.parse import ParseResult

with open('1.json','r',encoding='utf8') as f:
     list = json.load(f)
print(len(list))