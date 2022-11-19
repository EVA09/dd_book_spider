import random
import re
import time
import webbrowser
from datetime import datetime
import traceback
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm.auto import tqdm

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.42"
}

get_cookie = """
【获取关键cookie】
打开浏览器访问https://book.dangdang.com/ 并 “登录”
按下F12 或 自行打开浏览器开发者工具
点击console 于”>“处 粘贴以下内容，并敲击回车。
-------------------内容分割线----------------------
let input = document.createElement('input');
document.body.appendChild(input);
input.value = document.cookie;
input.select();
document.execCommand('copy');
console.log('获取完成，请返回命令行窗口继续执行！')
-------------------内容分割线----------------------
【系统将会自动复制所需cookie信息到你的剪贴板】
"""


def clear_dd(item, info):
    text = item.text
    text = text.replace("：", ":")
    if re.search("书号|ISBN", text, flags=re.I):
        info["书号"] = text.split(":")[1]
    elif text.find("所属分类") != -1:
        temp = text.split(":")
        more_info = re.sub("\s", "", temp[1])
        info[re.sub("\s", "", temp[0])] = "\r\n".join(more_info.split("图书>")).strip()
    else:
        temp = text.split(":")
        info[re.sub("\s", "", temp[0])] = re.sub("\s", "", temp[1])
    return info


def check_key(info, select, name, default="无搜索结果"):
    if len(select) > 0:
        info[name] = re.sub("\s", "", select[0].text)
    else:
        info[name] = default
    return info


def get_dd(url):
    if url.find("product.dangdang.com") == -1:
        return False
    url = url.strip()
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return False

    bs = BeautifulSoup(res.text, "html.parser")
    info = {}
    check_key(info, bs.select("#product_info>.name_info>h1"), "书名")
    temp = info["书名"].replace("（", "(").replace("）", "").split("(")
    info["书名"] = temp[0]
    info["书名信息"] = temp[1] if len(temp) > 1 else "无"
    check_key(info, bs.select("#dd-price"), "当当价")
    check_key(info, bs.select("#original-price"), "原价")
    for item in bs.select("#detail_describe ul li"):
        clear_dd(item, info)
    for item in bs.select(".messbox_info>.t1"):
        clear_dd(item, info)
    return info


def work(work_list):
    tqdm(desc="程序工作ing", dynamic_ncols=True)
    df = pd.DataFrame()
    error = 0
    for item in tqdm(work_list):
        try:
            temp = get_dd(item)
        except Exception as e:
            with open("error.log", "a+") as f:
                f.write("【url】%s" % item)
                f.write("\n")
                f.write(traceback.format_exc())
            error += 1
            continue
        if not temp:
            error += 1
            continue
        temp["地址"] = item
        temp = pd.DataFrame(temp, index=[0])
        try:
            df = pd.concat([df, temp], ignore_index=True)
        except:
            print(temp)
    if error != 0:
        print("【当前录入数据中有%s条无法正常获取】" % error)
    path = "dangdang数据%s %s.xlsx" % (
        random.randint(100, 999),
        datetime.now().strftime("%Y-%m-%d %H点%M"),
    )
    df.to_excel(path)
    print("【爬取完成，输出文件为：%s】" % path)
    return df


if __name__ == "__main__":
    print("【请批量粘贴需要爬取的dangdang网址，粘贴完成后敲击回车】")
    work_list = []
    while True:
        k = input().strip()
        if k == "":
            print("输入（Y或y）完成，输入（N或n）继续粘贴地址")
        elif k == "y" or k == "Y":
            break
        elif k == "N" or k == "n":
            continue
        elif re.search("^http", k):
            work_list.append(k)
    if len(work_list) > 0:
        print("【检测到有效输入地址：%s条】" % len(work_list))
        print(get_cookie)
        input("【敲击任意键后将尝试自动打开浏览器】")
        webbrowser.open(work_list[0])
        while True:
            cookie = input("【请右键粘贴cookie，并敲击回车键：】")
            if len(cookie) > 0 and cookie.find("sessionID") != -1:
                headers["Cookie"] = cookie
                print("\n")
                work(work_list)
                break
            else:
                print("【请输入有效的cookie】")
                continue
    else:
        print("【未检测到有效地址，请按一行一地址,整理好网址并保证以http开头后再次尝试】")
    input("【敲击任意键结束~】")
