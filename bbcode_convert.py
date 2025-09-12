import re


def bbcode_to_html(text: str) -> str:
    # 定义 BBCode 转换规则
    rules = [
        (r"\[b\](.*?)\[/b\]", r"<strong>\1</strong>"),
        (r"\[i\](.*?)\[/i\]", r"<em>\1</em>"),
        (r"\[u\](.*?)\[/u\]", r"<u>\1</u>"),
        (r"\[s\](.*?)\[/s\]", r"<del>\1</del>"),
        (r"\[url=(.*?)\](.*?)\[/url\]", r'<a href="\1">\2</a>'),
        (r"\[img\](.*?)\[/img\]", r'<img src="\1" alt="" />'),
        (r"\[quote\](.*?)\[/quote\]", r"<blockquote>\1</blockquote>"),
        (r"\[code\](.*?)\[/code\]", r"<pre><code>\1</code></pre>"),
        (r"\[color=(.*?)\](.*?)\[/color\]", r'<span style="color:\1">\2</span>'),
        (r"\[size=(.*?)\](.*?)\[/size\]", r'<span style="font-size:\1">\2</span>'),
    ]

    # 逐个应用规则
    for pattern, repl in rules:
        text = re.sub(pattern, repl, text, flags=re.DOTALL | re.IGNORECASE)

    # 再来一次
    for pattern, repl in rules:
        text = re.sub(pattern, repl, text, flags=re.DOTALL | re.IGNORECASE)

    pretext = '<div class="bbcode_container">'
    posttext = "</div>"
    style = """
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
</style>"""
    return pretext + text + posttext + style
