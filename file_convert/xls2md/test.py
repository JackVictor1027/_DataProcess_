import pandas as pd
from tabulate import tabulate

# 使用panda读取Excel文件
df = pd.read_excel('1.xlsx')

# panda解析，将空白单元格填充为“无数据”
df.fillna('无数据', inplace=True)

# headers='keys'表示第一行作为表头，pipe模式的作用是使结果以markdown表格格式输出
md_table = tabulate(df, headers='keys', tablefmt='pipe')

# 存储到文件
with open('1.md', 'w', encoding='utf-8') as f:
    f.write(md_table)