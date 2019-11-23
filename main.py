#!/usr/bin/python3
import requests
import sys
import feedparser
import json
import os

check = False  # 翻訳やslack投稿をしないでarxived.txtのみ更新する


def summarize(s):
    return s \
        .replace("\r", "") \
        .replace("\n", " ") \
        .replace("  ", " ") \
        .replace(". ", ".\r\n") \
        .replace(".\n", ".\r\n") \
        .replace(".\t", ".\r\n") \
        .replace("! ", "!\r\n") \
        .replace("!\n", "!\r\n") \
        .replace("!\t", "!\r\n") \
        .replace("? ", "?\r\n") \
        .replace("?\n", "?\r\n") \
        .replace("?\t", "?\r\n") \
        .replace("Fig.\r\n", "Fig. ") \
        .replace("et al.\r\n", "et al. ") \
        .replace("et al,.\r\n", "et al. ")


def translate(text):
    if check:
        return text
    resp = requests.get("https://translate.googleapis.com/translate_a/single", params={
        "client": "it",
        "sl": "en",
        "tl": "ja",
        "dt": "t",
        "ie": "UTF-8",
        "oe": "UTF-8",
        "dj": "1",
        "otf": "2",
        "q": text}, headers={
        "Host": "translate.googleapis.com",
        "User-Agent": "GoogleTranslate/5.9.59004 (iPhone; iOS 10.2; ja; iPhone9,1)",
        "Accept": "*/*",
        "Accept-Language": "ja-JP,en-US,*"
    })
    trans = json.loads(resp.text)
    s = ""
    for sentence in trans["sentences"]:
        s += sentence["trans"]
    return s


def get_bunsyou(entry):
    summary = summarize(entry["summary"][3:][:-4])  # pタグ除去してから整形したもの
    trans = translate(summary)  # 翻訳後
    # 翻訳前を投稿したいなら下記の{trans}を{summary}にすること
    return f'''-----------------------
{entry["id"]}
{entry["title"]}
{trans}
'''


def main():
    if os.path.isfile('arxived.txt'):
        with open('arxived.txt', 'r') as f:
            arxived = [x[:-1] for x in f.readlines()]  # arxived list
    else:
        with open('arxived.txt', 'x'):
            arxived = []
    with open('arxived.txt', 'a+') as f:
        root = feedparser.parse(sys.argv[1])
        for r in root["entries"]:
            if not r["id"] in arxived:  # 既に投稿したものか
                print(f'New arXiv!!! {r["id"]}')
                f.write(r["id"] + "\n")
                bunsyou = get_bunsyou(r)
                if not check:
                    resp = requests.post(sys.argv[2],
                                         data={"payload": {"text": bunsyou}.__str__()})
                    if resp.status_code != 200:
                        print("ERROR: Failed to post to slack!!")
            else:
                print(f'Not arXiv... {r["id"]}')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"./{sys.argv[0]} [arxiv RSS URL] [webhook url] [check]")
        exit()
    if len(sys.argv) > 3:
        check = True
    main()
