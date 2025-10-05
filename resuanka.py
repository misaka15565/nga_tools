# 安价统计脚本

import NGAClient
import pandas as pd
import argparse


def html_and_bbcode_cleaner(text):
    import re

    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")

    # 移除HTML标签
    text = re.sub(r"<[^>]+>", "", text)

    # 移除bbcode的img标签及其中的链接
    text = re.sub(r"\[img\].*?\[/img\]", "", text, flags=re.DOTALL)

    # 移除BBCode标签
    text = re.sub(r"\[/?[^\]]+\]", "", text)

    # &quot换为"
    text = text.replace("&quot;", '"')

    return text.strip()


anjia_meta = {
    "hbrgo": {
        "tid": 41989465,
        "start_lou": 33540,
        "ignore_author_user": [62906407],  # 忽略作者本人的帖子
        "keyword": None,  # 关键词过滤，不包括关键词的楼层不统计
        "endtime": "2025-09-16 18:00",  # 结束时间，格式为"YYYY-MM-DD HH:MM"，None为不限制时间
        "not_anjia_lou_list": [
            33586,
            33567,
            33590,
            33593,
            33582,
            33585,
            33589,
            33597,
            33615,
            33621,
            33622,
            33623,
            33624,
            33629,
            33632,
            33641,
            33642,
            33655,
            33659,
            33660,
            33664,
            33671,
            33675,
            33680,
            33681,
            33682,
            33684,
            33685,
            33689,
            33692,
            33695,
        ],
    },
    "gmgo": {
        "tid": 43877379,
        "start_lou": 7483,
        "ignore_author_user": [62668270],  # 忽略作者本人的帖子
        "keyword": None,  # 关键词过滤，不包括关键词的楼层不统计
        "endtime": "2025-09-17 21:21",  # 结束时间，格式为"YYYY-MM-DD HH:MM"，None为不限制时间
        "not_anjia_lou_list": [
            7488,
            7494,
            7524,
            7521,
            7516,
            7520,
            7523,
            7515,
            7517,
            7518,
            7519,
            7508,
            7525,
            7526,
            7529,
            7536,
            7537,
            7558,
            7559,
            7563,
            7565,
            7567,
            7569,
            7548,
            7549,
            7527,
            7562,
            7564,
            7571,
            7573,
            7575,
            7577,
            7560,
            7550,
            7535,
            7551,
            7552,
            7547,
            7568,
            7570,
            7566,
            7574,
            7576,
        ],
    },
}


def main():

    parser = argparse.ArgumentParser(description="安价统计脚本，生成安价.xlsx文件")
    parser.add_argument(
        "--anke",
        type=str,
        choices=anjia_meta.keys(),
        help="安价帖代号",
        default="hbrgo",
    )

    args = parser.parse_args()

    tid = anjia_meta[args.anke]["tid"]
    start_lou = anjia_meta[args.anke]["start_lou"]
    ignore_author_user = anjia_meta[args.anke]["ignore_author_user"]
    keyword = anjia_meta[args.anke]["keyword"]
    endtime = anjia_meta[args.anke]["endtime"]

    not_anjia_lou_list = anjia_meta[args.anke]["not_anjia_lou_list"]

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

    if len(content_list) != content_list[-1]["lou"] - start_lou + 1:
        print("Warning: 楼层数与实际帖子数不符，可能存在吞楼")
        except_lou_list = [i for i in range(start_lou, content_list[-1]["lou"] + 1)]
        for content in content_list:
            if content["lou"] in except_lou_list:
                except_lou_list.remove(content["lou"])
        print(f"缺失楼层列表: {list(except_lou_list)}")

    anjia_list = []
    ignored_anjia_list = []
    # 元素为{ "authorid": int,"authorname":str, "content": list[(int,str)]}
    # 其中content为该作者的所有安价内容，int为楼层，str为内容
    for content in content_list:
        this_anjia = {
            "authorid": content["author"]["uid"],
            "authorname": content["author"]["username"],
            "content": [(content["lou"], content["content"])],
        }

        ignore_cond = [
            (
                content["lou"] <= start_lou,
                f"楼层 {content['lou']} 小于等于起始楼层 {start_lou}",
            ),
            (
                content["author"]["uid"] in ignore_author_user,
                f"作者{content['author']['username']}在忽略名单中",
            ),
            (
                endtime is not None and content["postdate"] > endtime,
                f"时间 {content['postdate']} 超过截止时间 {endtime}",
            ),
            (
                content["lou"] in not_anjia_lou_list,
                f"楼层 {content['lou']} 在忽略楼层名单中",
            ),
        ]

        ignore_this = False
        for cond, reason in ignore_cond:
            if cond:
                print(f"忽略楼层 {content['lou']}，原因：{reason}")
                this_anjia["ignore_reason"] = reason
                ignore_this = True
                break
        if ignore_this:
            ignored_anjia_list.append(this_anjia)
            continue

        if keyword is None or keyword in content["content"]:

            have_same_author_anjia = False
            # 查找前面有没有同一作者的安价
            for i in range(len(anjia_list)):
                if anjia_list[i]["authorid"] == this_anjia["authorid"]:
                    # 找到同一作者的安价，合并内容
                    anjia_list[i]["content"].extend(this_anjia["content"])
                    have_same_author_anjia = True
                    print(
                        f"注意有同作者的重复安价请人工检查: {this_anjia['content'][0]}"
                    )
                    break

            if not have_same_author_anjia:
                anjia_list.append(this_anjia)

    print(f"总安价数: {len(anjia_list)}")
    print(f"总忽略楼层数: {len(ignored_anjia_list)}")
    print(f"总楼层数: {len(content_list)}")
    if len(anjia_list) + len(ignored_anjia_list) != len(content_list):
        print("Warning: 安价数与总楼层数不符，请检查忽略名单是否正确")

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
            maybe_repeat = "是" if len(anjia["content"]) > 1 else ""
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

    df_ignored = pd.DataFrame(
        columns=[
            "作者ID",
            "作者名称",
            "楼层",
            "内容",
            "忽略原因",
        ]
    )

    for ignored_anjia in ignored_anjia_list:
        for i in range(len(ignored_anjia["content"])):
            assert i == 0
            lou, content = ignored_anjia["content"][i]
            content = html_and_bbcode_cleaner(content)
            df_ignored = pd.concat(
                [
                    df_ignored,
                    pd.DataFrame(
                        {
                            "作者ID": [ignored_anjia["authorid"]],
                            "作者名称": [ignored_anjia["authorname"]],
                            "楼层": [lou],
                            "内容": [content],
                            "忽略原因": [ignored_anjia.get("ignore_reason", "")],
                        }
                    ),
                ],
                ignore_index=True,
            )

    with pd.ExcelWriter(f"{args.anke}_安价.xlsx", engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)
        wrap_format = writer.book.add_format({"text_wrap": True})
        # 设置列宽
        worksheet = writer.sheets["Sheet1"]
        worksheet.set_column("B:B", 10)
        worksheet.set_column("C:C", 15, wrap_format)
        worksheet.set_column("E:E", 100)
        worksheet.set_column("F:F", 20)

        # 设置每一行的行高
        for i in range(len(df)):
            # 根据内容估算行高

            content_length = len(df.at[i, "安价内容"])
            estimated_lines = content_length // 100 + 1

            worksheet.set_row(i + 1, estimated_lines * 50)

            # 如果这一行有可能重复安价，则设置用户名单元格为红色字体并加粗背景黄色
            if df.at[i, "是否有可能重复安价"] == "是":
                red_format = writer.book.add_format(
                    {
                        "font_color": "red",
                        "bold": True,
                        "bg_color": "yellow",
                        "text_wrap": True,
                    }
                )
                worksheet.write(i + 1, 2, df.at[i, "作者名称"], red_format)

        worksheet.set_column("E:E", 100, wrap_format)

        df_ignored.to_excel(writer, sheet_name="Ignored", index=False)
        worksheet_ignored = writer.sheets["Ignored"]
        worksheet_ignored.set_column("B:B", 10)
        worksheet_ignored.set_column("D:D", 100, wrap_format)
        for i in range(len(df_ignored)):
            content_length = len(df_ignored.at[i, "内容"])
            estimated_lines = content_length // 100 + 1
            worksheet_ignored.set_row(i + 1, estimated_lines * 25)


if __name__ == "__main__":
    main()
