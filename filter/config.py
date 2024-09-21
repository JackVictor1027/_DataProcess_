RAW_HTML_PATH="" #原始HTML文档路径
PURIED_JSON_PATH="jsons/" #处理最终得到的JSON
ID_AND_CLASS_TAGS = ["footer", "sidebar","navigation-bar","banner","foot-bar","wrapper header",
			   "t-top","c header","f-nav c","wrapper footer","wrapper nav wp-navi","nav",
			   "navbar uk-navbar-transparent uk-sticky","head","foot","header clearfix",
			   "footer clearfix","nav_min showhead","ind_navigationbg","menu-ul","erjicaidan l",
               "logo_menu_bj"
			   ]

FUZZY_TAGS = ["foot","head"] #模糊匹配标签

TOP_K=5 # 使用jieba分词进行词频排名后，需要返回几个权重最大的词

LOCAL_MODEL="qwen2" #使用何种本地大模型进行文章属性的生成

SCHOOL_ID=""
SCHOOL_NAME=""
SCHOOL_SIMPLE=""

PROMPT_OF_ATTRS='''
                阅读以下的HTML文档，阅读文章前1000字，生成一个不多于35字的标题title，分析文章属于何种类别category，并提取出本篇文章的发布时间publish_date。
                结果必须以如下json格式返回,请不要有其他的文字:
                {
                    "title":title,
                    "category":category,
                    "publish_date":publish_data,
                }
                如果遭遇无法生成的情况，给对应的属性值赋为null即可:\n
            '''

MAXNUM_PROCESSES = 3
SLEEP_TIME = 0.05
