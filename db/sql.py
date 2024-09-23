import os
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'config.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)

class Filter_Config(db.Model):  # 表名将会是 user（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True)  # 主键
    raw_html_path = db.Column(db.String, nullable=False)
    puried_json_path = db.Column(db.String, nullable=False)
    id_and_class_tags = db.Column(db.String, nullable=False)
    local_model = db.Column(db.String, nullable=False)
    school_name = db.Column(db.String, nullable=False)
    school_simple = db.Column(db.String, nullable=False)
    maxnum_processes = db.Column(db.Integer, nullable=False)

# db.create_all()