# 使用说明

`filter`:作用是将原始HTML中所有的样式代码，和不含有有效信息的标签都删去，只保留文章的主体内容，并转换为机器友好的MD文档。

`file_convert`:将word,excel,ppt,pdf,txt都转换为md（当然，你也可以在这里直接上传md），其中由于ppt格式文件难以被机器解析，故将先采用本地Office软件将其转换为zip压缩包格式的pptx文件，再引用第三方库将其转换为md。

> 2024年10月1日,本项目当前除了ppt以外的支持文档,都可以较为理想地保存文档中的图片.

# 启动步骤

1. 首先，最好保证Python版本为3.10，并安装项目必要的包:
> pip install -r requirements.txt

2. 之后，由于HTML数据过滤需要使用到本地大模型，本项目默认使用的部署工具是`ollama`，你需要保证在配置前，已经安装了ollama，并在本地部署了至少一个模型。
> 官网下载ollama:https://ollama.com/
> 
> 假设我们使用的是本地模型qwen2.5
> 
> ```ollama run qwen2.5```

3. 运行`db`包下的`sql.py`文件，初始化数据库

4. 运行前端，进行配置
> flask run

5. 点击启动就可以了，方便展示进度，你也可以直接在`filter`包下直接启动`main.py`,或者运行`file_convert`包下的`server_distribute.py`文件，在控制台查看实时进度和报错情况。

# TODO
- [ ] 多线程异步执行，提高任务执行速度
- [x] 前端UI界面，对用户更加友好，配置操作也更加便捷
- [x] 加入图片下载功能，每一份MD都以独立的包来保存(md+images)
- [x] 封装FileConvert类，重构代码
- [ ] 补充更多注释
- [x] 路径问题
- [ ] 提升文档转换效果,修复ppt2md时无法保存图片的bug
- [ ] 恢复文章中包含的关联链接(限< a >标签)
- [ ] 一键清理处理记录

更多使用说明，有待补充。