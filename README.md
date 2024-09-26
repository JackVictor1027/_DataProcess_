# 使用说明

`filter`:作用是将原始HTML中所有的样式代码，和不含有有效信息的标签都删去，只保留文章的主体内容，并转换为机器友好的MD文档。目前还不支持下载保留图片。

`file_convert`:将doc,docx,xls,xlsx,pdf都转换为md，其中由于doc,xls等Microsoft二进制格式文件难以被机器解析，故将先采用本地Office软件将其转换为XML格式的docx,xlsx文件，再引用第三方库将其转换为md。

其中，由于解析pdf所用的MinerU项目足够强大，能够将pdf中所有的图片一并保存下来。

# TODO
- [x] 多线程异步执行，提高任务执行速度
- [x] 前端UI界面，对用户更加友好，配置操作也更加便捷
- [ ] 加入图片下载功能，每一份MD都以独立的包来保存(md+images)
- [ ] 封装FileConvert类，重构代码

更多使用说明，有待补充。