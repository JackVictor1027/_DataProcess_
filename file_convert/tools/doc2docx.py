import win32com.client


def convert_doc_to_docx(doc_path, docx_path):
    # 创建 Word 应用程序对象
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False  # 不显示 Word 程序

    # 打开 .doc 文件,最好使用绝对路径
    doc = word.Documents.Open(doc_path)

    # 保存为 .docx 文件
    doc.SaveAs(docx_path, FileFormat=16)  # FileFormat=16 表示 .docx 格式

    # 关闭文件
    doc.Close()

    # 关闭 Word 应用程序
    word.Quit()