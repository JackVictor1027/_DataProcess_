import os
import sys

from flask import render_template, request

# 获取当前脚本的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到系统路径
sys.path.append(project_root)
from filter.main import main as filter_main
from file_convert.server_distribute import main as convert_main
from db.sql import app,Filter_Config,Convert_Config,db
@app.route('/')
def default():
    return render_template('index.html')

@app.route('/filter')
def filter():
    # 数据回显
    config = Filter_Config.query.get(1)
    return render_template('filter.html',config=config)

@app.route('/filter/update',methods=['GET','POST'])
def update_filter():
    # 获取请求体信息
    Info_update = request.json.get('Config')
    print(Info_update)
    # 在数据表中修改配置信息
    Config = Filter_Config.query.get(1)
    Config.raw_html_path = Info_update["raw_html_path"]
    Config.puried_json_path = Info_update["puried_json_path"]
    Config.local_model = Info_update["local_model"]
    Config.school_name = Info_update["school_name"]
    Config.school_simple = Info_update["school_simple"]
    Config.maxnum_processes = Info_update["maxnum_processes"]
    db.session.commit()
    return "Successfully"
    # filter_main()

@app.route('/filter/start')
def statr_filter():
    filter_main()

@app.route('/file_convert')
def file_convert():
    config = Convert_Config.query.get(1)
    return render_template('file_convert.html',config=config)

@app.route('/file_convert/update',methods=['GET','POST'])
def update_convert():
    # 获取请求体信息
    Info_update = request.json.get('Config')
    print(Info_update)
    # 在数据表中修改配置信息
    Config = Filter_Config.query.get(1)
    Config.all_files_path = Info_update["all_files_path"]
    Config.common_output_path = Info_update["common_output_path"]
    Config.school_name = Info_update["school_name"]
    Config.school_simple = Info_update["school_simple"]
    Config.maxnum_processes = Info_update["maxnum_processes"]
    return "Successfully"
    # convert_main()

@app.route('/file_convert/start')
def start_convert():
    convert_main()