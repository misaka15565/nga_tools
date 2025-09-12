# config模版
BASE_URL = "https://bbs.nga.cn"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"

# nga网站个人cookie项目
NGAPASSPORTUID = ""
NGAPASSPORTCID = ""


# 保存目录
OUTPUT_DIR = "output"


# html模板

HTML_PRE = '<div class="bbcode_container">'
HTML_POST = "</div>"
HTML_STYLE = """
<style>
.bbcode_container {
  max-width: 90%;   /* 占屏幕宽度的 90% */
  margin: 0 auto;
}
.bbcode_container img {
  max-width: 100%;    /* 图片不超过正文宽度 */
  height: auto;       /* 保持比例 */
}
blockquote {
  background: #f2eddf;
  border: 1px solid #e6e1d3;
}
</style>
"""
