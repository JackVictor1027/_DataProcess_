# 使用说明

`filter`:作用是将原始HTML中所有的样式代码，和不含有有效信息的标签都删去，只保留文章的主体内容，并转换为机器友好的MD文档。目前还不支持下载保留图片。

`file_convert`:将doc,docx,xls,xlsx,pdf都转换为md，其中由于doc,xls等Microsoft二进制格式文件难以被机器解析，故将先采用本地Office软件将其转换为XML格式的docx,xlsx文件，再引用第三方库将其转换为md。

其中，由于解析pdf所用的MinerU项目足够强大，能够将pdf中所有的图片一并保存下来。

更多使用说明，有待补充。