import argparse
from time import sleep
import hashlib
from NGAClient import NGAClient
import os
import config
import json
import bbcode_convert
from PIL import Image
import requests
import re
from bs4 import BeautifulSoup


def get_folder(tid, aid):
    folder = config.OUTPUT_DIR + "/" + tid + "_" + (aid if aid else "all")
    os.makedirs(folder, exist_ok=True)
    return folder


def json_download_page(tid, aid, page):
    nga_client = NGAClient()

    json_output_folder = get_folder(tid, aid) + "/json"
    os.makedirs(json_output_folder, exist_ok=True)

    res = nga_client.get_page(tid, aid, page)
    with open(f"{json_output_folder}/page_{page}.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=4)


def json_download_all(tid, aid):
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


def bbcode_extract_page(tid, aid, page):
    json_folder = get_folder(tid, aid) + "/json"
    bbcode_output_folder = get_folder(tid, aid) + "/bbcode"
    os.makedirs(bbcode_output_folder, exist_ok=True)
    lou_list = []
    file = f"page_{page}.json"
    with open(f"{json_folder}/{file}", "r", encoding="utf-8") as f:
        data = json.load(f)
        result = data.get("result", [])
        for item in result:
            lou = item["lou"]
            if lou == None:
                raise ValueError(f"Missing 'lou' in post data while processing {file}")
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


# 单个图片下载函数
def img_download(url, save_folder):
    # 调用curl
    os.makedirs(save_folder, exist_ok=True)
    filename = url.split("/")[-1]
    save_path = os.path.join(save_folder, filename)

    for _ in range(5):  # 最多尝试5次
        # 检测文件是否存在，存在则跳过
        if os.path.exists(save_path):
            print(f"Image already exists, skipping url: {url}")
            return
        try:
            os.system(f'curl "{url}" -o "{save_path}"')
            # 检查下载的图片是否能读取
            img = Image.open(save_path)
            img.verify()  # 验证图片是否损坏
        except Exception as e:
            img.close()
            print(f"Failed to download image {url}: {e}")
            os.remove(save_path)  # 删除损坏的文件


def nga_imgurl_verify(url) -> bool:
    # 检测是否是nga的图片链接
    # 例如 https://img.nga.178.com/attachments/mon_202507/30/lsQknd-6gnlK9ToS4s-8c.webp
    # 前面是https://img.nga.178.com/attachments/
    # 然后是mon_yyyymm/dd/
    # 然后是文件名

    pattern = r"^https://img\.nga\.178\.com/attachments/mon_\d{6}/\d{2}/[\w\-.]+\.(jpg|jpeg|png|gif|bmp|webp)$"
    return re.match(pattern, url) is not None


def bbcode_img_download(tid, aid, page=None):
    bbcode_folder = get_folder(tid, aid) + "/bbcode"
    img_folder = get_folder(tid, aid) + "/images"
    os.makedirs(img_folder, exist_ok=True)

    img_urls = []

    file_list = os.listdir(bbcode_folder)
    if page != None:
        file_list = []
        for i in range(20):
            if os.path.exists(f"{bbcode_folder}/post_{(page-1)*20+i}.bbcode"):
                file_list.append(f"post_{(page-1)*20+i}.bbcode")

    for file in file_list:
        if file.endswith(".bbcode"):
            with open(f"{bbcode_folder}/{file}", "r", encoding="utf-8") as f:
                content = f.read()
                # 提取图片链接
                urls = re.findall(r"\[img\](.*?)\[/img\]", content, re.IGNORECASE)
                img_urls.extend(urls)

    filename_url_dict = {}
    for url in img_urls:
        # 检查url是否合法
        if not nga_imgurl_verify(url):
            print(f"Invalid NGA image URL, skipping: {url}")
            continue

        filename = url.split("/")[-1]
        # 检查文件名是否已经存在，如果存在则print
        if filename in filename_url_dict and filename_url_dict[filename] != url:
            print(
                f"Duplicate filename found: {filename} for URLs: {filename_url_dict[filename]} and {url}"
            )
        else:
            filename_url_dict[filename] = url
    print("图片总数:", len(img_urls))
    print("去重后图片数:", len(filename_url_dict))

    already_downloaded_imgs_list = os.listdir(img_folder)

    # 下载没下过的图片
    for filename, url in filename_url_dict.items():
        if filename not in already_downloaded_imgs_list:
            print(f"Downloading image: {url}")
            img_download(url, img_folder)


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


def bbcode2html2pdf(tid, aid, page=None):
    POST_PER_PAGE = 20
    bbcode_folder = get_folder(tid, aid) + "/bbcode"
    pdf_output_folder = get_folder(tid, aid) + "/pdf"
    os.makedirs(pdf_output_folder, exist_ok=True)

    bbcode_files = os.listdir(bbcode_folder)
    bbcode_files.sort(key=lambda x: int(x.split("_")[-1].split(".")[0]))
    bbcode_from = bbcode_files[0].split("_")[-1].split(".")[0]
    bbcode_to = bbcode_files[-1].split("_")[-1].split(".")[0]

    if page == None:
        for i in range(
            int(bbcode_from) // POST_PER_PAGE + 1, int(bbcode_to) // POST_PER_PAGE + 2
        ):
            bbcode2html2pdf(tid, aid, page=i)
        return

    page = int(page)
    start_lou = (page - 1) * POST_PER_PAGE
    end_lou = start_lou + POST_PER_PAGE - 1

    if end_lou > int(bbcode_to):
        end_lou = int(bbcode_to)

    html_parts = {}
    for i in range(start_lou, end_lou + 1):
        bbcode_file = f"post_{i}.bbcode"
        if os.path.exists(f"{bbcode_folder}/{bbcode_file}"):
            with open(f"{bbcode_folder}/{bbcode_file}", "r", encoding="utf-8") as f:
                content = f.read()
                html_content = bbcode_convert.bbcode_to_html(content)
                html_parts[i] = html_content
        else:
            print(f"Warning: {bbcode_file} does not exist, skipping.")
            html_parts[i] = "<p>此楼层内容缺失</p>"

    # 组合html，在每层前添加楼层标记
    for lou in html_parts:
        html_parts[lou] = f"<h2>第{lou}楼</h2>\n" + html_parts[lou]
    full_html = (
        "<html><head><meta charset='utf-8'>"
        + config.HTML_STYLE
        + "</head><body>"
        + config.HTML_PRE
        + "".join(html_parts.values())
        + config.HTML_POST
        + "</body></html>"
    )

    local_imgs = os.listdir(get_folder(tid, aid) + "/images")

    # 将html中的图像url替换为本地路径
    soup = BeautifulSoup(full_html, "html.parser")
    for img in soup.find_all("img"):
        img_url = img.get("src")
        filename = img_url.split("/")[-1]
        local_path = f"../images/{filename}"
        img["src"] = local_path  # 修改img标签的src属性

        if not nga_imgurl_verify(img_url):
            print(
                f"Warning: Image URL {img_url} is not a valid NGA image URL in page {page}."
            )
            a = input("input anything to continue")

    full_html = str(soup)

    # 暂存html供调试
    with open(
        f"{pdf_output_folder}/page_{page}_debug.html", "w", encoding="utf-8"
    ) as f:
        f.write(full_html)

    # 保存为pdf，使用命令行调用weasyprint

    output_pdf_path = f"{pdf_output_folder}/page_{page}.pdf"
    os.system(
        f"weasyprint {pdf_output_folder}/page_{page}_debug.html {output_pdf_path}"
    )


def imgclear(tid, aid):
    # 删除不能正常读取的文件

    img_folder = get_folder(tid, aid) + "/images"
    for file in os.listdir(img_folder):
        if file.endswith((".jpg", ".png", ".jpeg", ".gif", ".bmp", ".webp")):
            file_path = os.path.join(img_folder, file)
            try:
                img = Image.open(file_path)
                img.verify()  # 验证图片是否损坏
            except (IOError, SyntaxError) as e:
                # 关闭文件，不然会报错
                img.close()
                print(f"Removing corrupted image: {file_path}")
                os.remove(file_path)


def single_page_download(tid, aid, page):
    json_download_page(tid, aid, page)
    bbcode_extract_page(tid, aid, page)
    bbcode_img_download(tid, aid, page)
    bbcode2html2pdf(tid, aid, page)
    pass


def same_img_finder(tid, aid):
    img_folder = get_folder(tid, aid) + "/images"
    hash_dict = {}

    file_list = os.listdir(img_folder)
    for file in file_list:
        file_path = os.path.join(img_folder, file)
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha1(f.read()).hexdigest()
            if file_hash in hash_dict:
                hash_dict[file_hash].append(file)
            else:
                hash_dict[file_hash] = [file]
    # 输出图片数
    # 输出不重复的图片数
    print(f"Total images: {len(file_list)}")
    print(f"Unique images: {len(hash_dict)}")
    return
    # 输出重复的图片
    for file_hash, files in hash_dict.items():
        if len(files) > 1:
            print(f"Duplicate images found: {files}")


def unique_img_gen(tid, aid):
    dict_path = (
        get_folder(tid, aid) + "/images_hash_dict.json"
    )  # 存储原文件名-hash.ext文件名映射
    img_folder = get_folder(tid, aid) + "/images"
    unique_img_folder = get_folder(tid, aid) + "/unique_images"
    os.makedirs(unique_img_folder, exist_ok=True)
    hash_dict = {}
    file_list = os.listdir(img_folder)
    for file in file_list:
        file_path = os.path.join(img_folder, file)
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha1(f.read()).hexdigest()
            hash_dict[file] = file_hash
    # 保存hash_dict
    with open(dict_path, "w", encoding="utf-8") as f:
        json.dump(hash_dict, f, ensure_ascii=False, indent=4)
    # 将图片复制到unique_img_folder，文件名为hash.ext
    for file, file_hash in hash_dict.items():
        ext = file.split(".")[-1]
        unique_file_path = os.path.join(unique_img_folder, f"{file_hash}.{ext}")
        if not os.path.exists(unique_file_path):
            os.system(f'cp "{os.path.join(img_folder, file)}" "{unique_file_path}"')


def main():
    parser = argparse.ArgumentParser(description="NGA Backupper")
    # 必选tid参数
    parser.add_argument("--tid", type=str, help="NGA Post ID to back up", required=True)
    # 可选aid参数
    parser.add_argument(
        "--aid", type=str, default=None, help="NGA Author ID to back up"
    )
    # 可选page参数
    parser.add_argument(
        "--page", type=int, default=None, help="NGA Page number to back up"
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="json",
        help="json:下载json；bbcode：从json提取bbcode；",
        choices=[
            "json",
            "bbcode",
            "bb2html",
            "imgdownload",
            "tj",
            "imgclear",
            "singlepage",
            "sameimgfinder",
            "uniqueimggen",
        ],
    )

    args = parser.parse_args()

    tid = args.tid
    aid = args.aid
    mode = args.mode

    print(f"NGA Post ID: {tid}")
    print(f"NGA Author ID: {aid}")

    if mode == "json":
        json_download_all(tid, aid)
    elif mode == "bbcode":
        bbcode_extract(tid, aid)
    elif mode == "bb2html":
        bbcode2html2pdf(tid, aid)
    elif mode == "imgdownload":
        bbcode_img_download(tid, aid)
    elif mode == "imgclear":
        imgclear(tid, aid)
    elif mode == "singlepage":
        if args.page == None:
            raise ValueError("Page number must be provided for singlepage mode.")
        single_page_download(tid, aid, args.page)
    elif mode == "sameimgfinder":
        same_img_finder(tid, aid)
    elif mode == "uniqueimggen":
        unique_img_gen(tid, aid)


if __name__ == "__main__":
    main()
