from db.sql import Convert_Config as cc


class Convert_Config:
    ALL_FILES_PATH="" # 等待转换的文档路径

    COMMON_OUTPUT_PATH=""

    SCHOOL_ID=""
    SCHOOL_NAME=""
    SCHOOL_SIMPLE=""

    WORK_DIRS = ['docx2md/','pdf2md/','xlsx2md/','pptx2md/','txt2md/','md/']

    CONVERT_EXTENSIONS=['.pdf','.doc','.docx','.xls','.xlsx']

    MAXNUM_PROCESSES = 5

    # 查询数据库，初始化得到实例
    def __init__(self):
        config = cc.query.get(1)
        self.ALL_FILES_PATH = config.all_files_path
        self.COMMON_OUTPUT_PATH = config.common_output_path
        self.SCHOOL_NAME = config.school_name
        self.SCHOOL_SIMPLE = config.school_simple
        self.MAXNUM_PROCESSES = config.maxnum_processes