import win32com.client


def convert_xls_to_xlsx(xls_path:str, xlsx_path:str):
    # 创建 Excel 应用程序对象
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False  # 不显示 Excel 程序

    # 更改路径表达形式->系统应用访问 : \\
    xls_path = xls_path.replace("/","\\")
    xlsx_path = xlsx_path.replace("/","\\")

    # 打开 .xls 文件,最好使用绝对路径
    xls = excel.Workbooks.Open(xls_path)

    # 保存为 .xlsx 文件
    xls.SaveAs(xlsx_path, FileFormat=51)  # FileFormat=51 表示 .xlsx 格式

    # 关闭文件
    xls.Close(SaveChanges=False)

    # 关闭 Excel 应用程序
    excel.Quit()

def test_xls2xlsx():
    xls = 'D:/TechDream/AI/AI_LLM_query/data/hbfu/files/lib.hbfu.edu.cn/1544149873959076559.xls'
    xlsx = 'D:/TechDream/AI/AI_LLM_query/data/hbfu/files/lib.hbfu.edu.cn/1544149873959076559.xlsx'
    convert_xls_to_xlsx(xls,xlsx)