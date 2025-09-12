import argparse
from time import sleep
from NGAClient import NGAClient
import os
import config
import json
import bbcode_convert


def get_folder(tid, aid):
    folder = config.OUTPUT_DIR + "/" + tid + "_" + (aid if aid else "all")
    os.makedirs(folder, exist_ok=True)
    return folder


def json_download(tid, aid):
    nga_client = NGAClient()

    json_output_folder = get_folder(tid, aid) + "/json"
    os.makedirs(json_output_folder, exist_ok=True)

    page = 1
    total_page_count = int(1e9)
    while True:
        res = nga_client.get_page(tid, aid, page)
        total_page_count = res.get("totalPage", total_page_count)
        with open(f"{json_output_folder}/page_{page}.json", "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=4)

        if page >= total_page_count:
            break
        page += 1


def bbcode_extract(tid, aid):
    json_folder = get_folder(tid, aid) + "/json"
    bbcode_output_folder = get_folder(tid, aid) + "/bbcode"
    os.makedirs(bbcode_output_folder, exist_ok=True)

    lou_list = []

    for file in os.listdir(json_folder):
        if file.endswith(".json"):
            with open(f"{json_folder}/{file}", "r", encoding="utf-8") as f:
                data = json.load(f)
                result = data.get("result", [])
                for item in result:
                    lou = item["lou"]
                    if lou == None:
                        raise ValueError(
                            f"Missing 'lou' in post data while processing {file}"
                        )
                    lou_list.append(lou)
                    content = item.get("content", "")
                    with open(
                        f"{bbcode_output_folder}/post_{lou}.bbcode",
                        "w",
                        encoding="utf-8",
                    ) as out_f:
                        out_f.write(content)
    lou_list.sort()
    # 检查lou_list是否连续，如果不连续则输出缺的数字
    # 理论上lou_list从0开始到最大值应该是连续的
    missing_lous = []
    for i in range(lou_list[0], lou_list[-1] + 1):
        if i not in lou_list:
            missing_lous.append(i)

    if missing_lous:
        print(f"Missing 'lou' numbers found: {missing_lous}")


import requests


# 单个图片下载函数
def img_download(url, save_folder):
    # 调用curl
    os.makedirs(save_folder, exist_ok=True)
    filename = url.split("/")[-1]
    save_path = os.path.join(save_folder, filename)
    # 检测文件是否存在，存在则跳过
    if os.path.exists(save_path):
        print(f"Image already exists, skipping: {save_path},url: {url}")
        return
    try:
        os.system(f'curl "{url}" -o "{save_path}"')

        # sleep(2)  # 避免请求过于频繁
    except requests.RequestException as e:
        print(f"Failed to download image {url}: {e}")


from bs4 import BeautifulSoup


def html_img_download(tid, aid):
    # 在html中提取出图片链接并下载
    html_folder = get_folder(tid, aid) + "/html"
    img_folder = get_folder(tid, aid) + "/images"
    os.makedirs(img_folder, exist_ok=True)

    imginfo_json_path = get_folder(tid, aid) + "/imginfo.json"
    # 如果文件不存在则创建一个空的
    if not os.path.exists(imginfo_json_path):
        with open(imginfo_json_path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    with open(imginfo_json_path, "r", encoding="utf-8") as f:
        imginfo = json.load(f)
    for file in os.listdir(html_folder):
        if file.endswith(".html"):
            print(f"----------Processing file: {file}----------")
            with open(f"{html_folder}/{file}", "r", encoding="utf-8") as f:
                content = f.read()
                # 尝试提取图片链接
                soup = BeautifulSoup(content, "html.parser")
                img_links = [img["src"] for img in soup.find_all("img", src=True)]
                for link in img_links:
                    print(f"Downloading image: {link}")
                    img_download(link, img_folder)
                    imginfo[link] = link.split("/")[-1]
                    with open(imginfo_json_path, "w", encoding="utf-8") as f:
                        json.dump(imginfo, f, ensure_ascii=False, indent=4)


def html_img_download_tj(tid, aid):
    # 在html中提取出图片链接并下载
    html_folder = get_folder(tid, aid) + "/html"
    sum = 0
    for file in os.listdir(html_folder):
        if file.endswith(".html"):
            with open(f"{html_folder}/{file}", "r", encoding="utf-8") as f:
                content = f.read()
                # 尝试提取图片链接
                soup = BeautifulSoup(content, "html.parser")
                img_links = [img["src"] for img in soup.find_all("img", src=True)]
                sum += len(img_links)
    print(sum)


def bbcode2html(tid, aid):
    bbcode_folder = get_folder(tid, aid) + "/bbcode"
    html_output_folder = get_folder(tid, aid) + "/html"
    os.makedirs(html_output_folder, exist_ok=True)

    for file in os.listdir(bbcode_folder):
        if file.endswith(".bbcode"):
            with open(f"{bbcode_folder}/{file}", "r", encoding="utf-8") as f:
                content = f.read()
                # TODO: bbcode转html
                html_content = bbcode_convert.bbcode_to_html(content)
                with open(
                    f"{html_output_folder}/{file.replace('.bbcode', '.html')}",
                    "w",
                    encoding="utf-8",
                ) as out_f:
                    out_f.write(html_content)


def imgclear(tid, aid):
    # 删除不能正常读取的文件
    from PIL import Image

    img_folder = get_folder(tid, aid) + "/images"
    for file in os.listdir(img_folder):
        if file.endswith((".jpg", ".png", ".jpeg", ".gif", ".bmp", ".webp")):
            file_path = os.path.join(img_folder, file)
            try:
                img = Image.open(file_path)
                img.verify()  # 验证图片是否损坏
            except (IOError, SyntaxError) as e:
                print(f"Removing corrupted image: {file_path}")
                os.remove(file_path)


def main():
    parser = argparse.ArgumentParser(description="NGA Backupper")
    # 必选tid参数
    parser.add_argument("--tid", type=str, help="NGA Post ID to back up", required=True)
    # 可选aid参数
    parser.add_argument(
        "--aid", type=str, default=None, help="NGA Author ID to back up"
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="json",
        help="json:下载json；bbcode：从json提取bbcode；",
        choices=["json", "bbcode", "bb2html", "imgdownload", "tj", "imgclear"],
    )

    args = parser.parse_args()

    tid = args.tid
    aid = args.aid
    mode = args.mode

    print(f"NGA Post ID: {tid}")
    print(f"NGA Author ID: {aid}")

    if mode == "json":
        json_download(tid, aid)
    elif mode == "bbcode":
        bbcode_extract(tid, aid)
    elif mode == "bb2html":
        bbcode2html(tid, aid)
    elif mode == "imgdownload":
        html_img_download(tid, aid)
    elif mode == "tj":
        html_img_download_tj(tid, aid)
    elif mode == "imgclear":
        imgclear(tid, aid)


if __name__ == "__main__":
    main()
