import hashlib
import os,re
import shutil

import fitz
import pandas as pd
import requests
from bs4 import BeautifulSoup
from docx import Document
from pptx import Presentation

from common.logger_setup import logger
from file_convert.pdf2md.main import pdf2md


class FileConvert:
    md_image_pattern = re.compile(r'!\[.*?\]\((.*?)\)')
    html_image_pattern = re.compile(r'<img\s+[^>]*?src=["\']([^"\']*)["\'][^>]*>')
    """封装所有文件读取操作。"""

    def __init__(self):
        self.image_suffix = ['.jpg', '.jpeg', '.png', '.bmp']
        self.md_suffix = '.md'
        self.text_suffix = ['.txt', '.text']
        self.excel_suffix = ['.xlsx', '.xls', '.csv']
        self.pdf_suffix = '.pdf'
        self.ppt_suffix = '.pptx'
        self.html_suffix = ['.html', '.htm', '.shtml', '.xhtml']
        self.word_suffix = ['.docx', '.doc']
        self.code_suffix = ['.py']
        self.normal_suffix = [self.md_suffix
                              ] + self.text_suffix + self.excel_suffix + [
                                 self.pdf_suffix
                             ] + self.word_suffix + [self.ppt_suffix
                                                     ] + self.html_suffix

    def save_image(self, uri: str, outdir: str):
        """
            保存图像URI到本地目录。
            如果失败，返回None。
        """
        images_dir = os.path.join(outdir, 'images')
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        md5 = hashlib.md5()
        md5.update(uri.encode('utf8'))
        uuid = md5.hexdigest()[0:6]
        filename = uuid + uri[uri.rfind('.'):]
        # 定义非法字符的正则表达式
        illegal_chars = r'["\\/*?<>|:]+'
        # 使用正则表达式替换非法字符
        filename = re.sub(illegal_chars, '', filename)

        relative_path = './images/'+filename
        image_path = os.path.join(images_dir, filename)

        logger.info('下载 {}'.format(uri))
        try:
            if uri.startswith('http'):
                resp = requests.get(uri, stream=True)
                if resp.status_code == 200:
                    with open(image_path, 'wb') as image_file:
                        for chunk in resp.iter_content(1024):
                            image_file.write(chunk)
            else:
                shutil.copy(uri, image_path)
        except Exception as e:
            logger.error(f"图片下载失败:uri{uri},错误原因:{e}")
            return None, None
        return uuid, relative_path

    def get_type(self, filepath: str):
        """根据URI后缀获取文件类型。"""
        filepath = filepath.lower()
        if filepath.endswith(self.pdf_suffix):
            return 'pdf'

        if filepath.endswith(self.md_suffix):
            return 'md'

        if filepath.endswith(self.ppt_suffix):
            return 'ppt'

        for suffix in self.image_suffix:
            if filepath.endswith(suffix):
                return 'image'

        for suffix in self.text_suffix:
            if filepath.endswith(suffix):
                return 'text'

        for suffix in self.word_suffix:
            if filepath.endswith(suffix):
                return 'word'

        for suffix in self.excel_suffix:
            if filepath.endswith(suffix):
                return 'excel'

        for suffix in self.html_suffix:
            if filepath.endswith(suffix):
                return 'html'

        for suffix in self.code_suffix:
            if filepath.endswith(suffix):
                return 'code'
        return None

    def md5(self, filepath: str):
        """计算文件的SHA-256哈希值。"""
        hash_object = hashlib.sha256()
        with open(filepath, 'rb') as file:
            chunk_size = 8192
            while chunk := file.read(chunk_size):
                hash_object.update(chunk)

        return hash_object.hexdigest()[0:8]

    def summarize(self, files: list):
        """总结文件处理结果。"""
        success = 0
        skip = 0
        failed = 0

        for file in files:
            if file.state:
                success += 1
            elif file.reason == 'skip':
                skip += 1
            else:
                failed += 1

        print.info('累计{}文件，成功{}个，跳过{}个，异常{}个'.format(len(files), success,
                                                                  skip, failed))

    def read_pdf(self, filepath: str):
        """读取PDF文件并序列化表格。"""
        # TODO
        pdf2md(filepath)

    def read_excel(self, filepath: str):
        """读取Excel文件并转换为JSON格式。"""
        # TODO
        table = None
        # 必须是绝对路径
        if filepath.endswith('.csv'):
            table = pd.read_csv(filepath)
        else:
            table = pd.read_excel(filepath)
        if table is None:
            return ''
        json_text = table.dropna(axis=1).to_json(force_ascii=False)
        return json_text

    def read_word(self, filepath: str) -> str:
        """
        读取 Word 文档的内容并转换为 Markdown 格式。
        :param filepath: 文件路径
        :return: Markdown 格式的字符串
        """
        doc = Document(filepath)
        markdown_content = ""
        for paragraph in doc.paragraphs:
            markdown_content += f"{paragraph.text}\n\n"
        return markdown_content

    def read_ppt(self, filepath: str) -> str:
        """
        读取 PPT 的所有幻灯片中的文本框内容并转换为 Markdown 格式。
        :param filepath: 文件路径
        :return: Markdown 格式的字符串
        """
        presentation = Presentation(filepath)
        markdown_content = ""
        for slide in presentation.slides:
            slide_title = slide.shapes.title.text if slide.shapes.title else "Slide Title"
            markdown_content += f"# {slide_title}\n\n"
            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                for paragraph in shape.text_frame.paragraphs:
                    markdown_content += f"{paragraph.text}\n\n"
        return markdown_content

    def read(self, filepath: str):
        """读取文件内容。"""
        file_type = self.get_type(filepath)

        text = ''

        if not os.path.exists(filepath):
            return text, None

        try:
            if file_type == 'md' or file_type == 'text':
                with open(filepath) as f:
                    text = f.read()

            elif file_type == 'pdf':
                text += self.read_pdf(filepath)

            elif file_type == 'excel':
                text += self.read_excel(filepath)

            elif file_type == 'word':
                text = self.read_word(filepath)
                if file_type == 'ppt':
                    text = text.replace('\n', ' ')

            elif file_type == 'ppt':
                text = self.read_word(filepath)
                if file_type == 'ppt':
                    text = text.replace('\n', ' ')

            elif file_type == 'html':
                with open(filepath) as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    text += soup.text

            elif file_type == 'code':
                with open(filepath, errors="ignore") as f:
                    text += f.read()

        except Exception as e:
            logger.error((filepath, str(e)))
            return '', e

        if file_type != 'code':
            text = text.replace('\n\n', '\n')
            text = text.replace('  ', ' ')
        return text, None
