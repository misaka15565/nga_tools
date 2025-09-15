# 安价统计脚本

import NGAClient
import pandas as pd


def html_and_bbcode_cleaner(text):
    import re

    # 移除HTML标签
    text = re.sub(r"<[^>]+>", "", text)

    # 移除bbcode的img标签及其中的链接
    text = re.sub(r"\[img\].*?\[/img\]", "", text, flags=re.DOTALL)

    # 移除BBCode标签
    text = re.sub(r"\[/?[^\]]+\]", "", text)

    # &quot换为"
    text = text.replace("&quot;", '"')

    return text.strip()


def main():
    tid = 41989465
    start_lou = 33540
    ignore_author_user = [62906407]  # 忽略作者本人的帖子
    keyword = "安价"  # 关键词过滤，不包括关键词的楼层不统计，None为不过滤
    endtime = (
        "2025-09-16 18:00"  # 结束时间，格式为"YYYY-MM-DD HH-MM-SS"，None为不限制时间
    )

    client = NGAClient.NGAClient()

    page = (start_lou) // 20 + 1

    print(f"Fetching page {page}...")
    page_first = client.get_page(tid, None, page)

    total_page = page_first["totalPage"]

    page_jsons = [page_first]

    for p in range(page + 1, total_page + 1):
        print(f"Fetching page {p}...")
        page_jsons.append(client.get_page(tid, None, p))

    content_list = []
    for page_json in page_jsons:
        content_list.extend(page_json["result"])

    print(len(content_list))

    anjia_list = []
    # 元素为{ "authorid": int,"authorname":str, "content": list[(int,str)]}
    # 其中content为该作者的所有安价内容，int为楼层，str为内容
    for content in content_list:
        if content["author"]["uid"] in ignore_author_user:
            continue

        if endtime is None or content["postdate"] > endtime:
            continue

        if keyword is None or keyword in content["content"]:

            this_anjia = {
                "authorid": content["author"]["uid"],
                "authorname": content["author"]["username"],
                "content": [(content["lou"], content["content"])],
            }

            have_same_author_anjia = False
            # 查找前面有没有同一作者的安价
            for i in range(len(anjia_list)):
                if anjia_list[i]["authorid"] == this_anjia["authorid"]:
                    # 找到同一作者的安价，合并内容
                    anjia_list[i]["content"].extend(this_anjia["content"])
                    have_same_author_anjia = True
                    break

            if not have_same_author_anjia:
                anjia_list.append(this_anjia)

    print(f"总安价数: {len(anjia_list)}")

    # 保存结果到安价.xlsx

    df = pd.DataFrame(
        columns=[
            "编号",
            "作者ID",
            "作者名称",
            "安价楼层",
            "安价内容",
            "是否有可能重复安价",
        ]
    )
    for anjia_it in range(len(anjia_list)):
        anjia = anjia_list[anjia_it]
        for i in range(len(anjia["content"])):
            lou, content = anjia["content"][i]
            content = html_and_bbcode_cleaner(content)
            maybe_repeat = "是" if len(anjia["content"]) > 1 else "否"
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        {
                            "编号": [anjia_it + 1],
                            "作者ID": [anjia["authorid"]],
                            "作者名称": [anjia["authorname"]],
                            "安价楼层": [lou],
                            "安价内容": [content],
                            "是否有可能重复安价": [maybe_repeat],
                        }
                    ),
                ],
                ignore_index=True,
            )

    with pd.ExcelWriter("安价.xlsx", engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)

        # 设置列宽
        worksheet = writer.sheets["Sheet1"]
        worksheet.set_column("B:B", 10)
        worksheet.set_column("C:C", 15)
        worksheet.set_column("E:E", 100)
        worksheet.set_column("F:F", 20)

        # 设置每一行的行高
        for i in range(len(df)):
            # 根据内容估算行高

            content_length = len(df.at[i, "安价内容"])
            estimated_lines = content_length // 100 + 1

            worksheet.set_row(i + 1, estimated_lines * 25)

        wrap_format = writer.book.add_format({"text_wrap": True})
        worksheet.set_column("E:E", 100, wrap_format)


if __name__ == "__main__":
    main()
