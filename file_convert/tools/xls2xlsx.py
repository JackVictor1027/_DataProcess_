import win32com


def convert_xls_to_xlsx(xls_path, xlsx_path):
    # 创建 Excel 应用程序对象
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False  # 不显示 Excel 程序

    # 打开 .xls 文件,最好使用绝对路径
    xls = excel.Workbooks.Open(xls_path)

    # 保存为 .xlsx 文件
    xls.SaveAs(xlsx_path, FileFormat=51)  # FileFormat=51 表示 .xlsx 格式

    # 关闭文件
    xls.Close(SaveChanges=False)

    # 关闭 Excel 应用程序
    excel.Quit()