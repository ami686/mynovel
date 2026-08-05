import os
import re
import html
import xml.etree.ElementTree as ET

XML_FILE = "wordpress.xml"
OUTPUT = "content"

short_map = {
    "民间故事": "folk",
    "睡前小故事": "bedtime",
    "超短故事": "micro",
    "笑话和幽默": "other",
    "笑话": "other",
}

ignore_categories = [
    "短篇",
    "连载",
    "小说",
]


book_ids = {}
book_titles = {}

short_counter = {
    "folk": 1,
    "bedtime": 1,
    "micro": 1,
    "other": 1
}


def clean_text(text):

    if not text:
        return ""

    text = html.unescape(text)

    text = re.sub(
        r'<!--.*?-->',
        '',
        text,
        flags=re.S
    )

    text = re.sub(
        r'\[.*?\]',
        '',
        text
    )

    return text.strip()


def get_book_id(name):

    if name not in book_ids:

        letters = "abcdefghijklmnopqrstuvwxyz"

        book_ids[name] = letters[len(book_ids)]

        book_titles[book_ids[name]] = name

    return book_ids[name]


def save_file(path, title, date, content):

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True
    )

    md = f"""---
title: "{title}"
date: {date}
---

{content}
"""

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(md)


def save_book_index(folder, title):

    path = os.path.join(
        folder,
        "_index.md"
    )

    md = f"""---
title: "{title}"
---

"""

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(md)



tree = ET.parse(XML_FILE)

root = tree.getroot()


ns = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wp": "http://wordpress.org/export/1.2/"
}



for item in root.findall(".//item"):

    post_type = item.find(
        "wp:post_type",
        ns
    )

    if post_type is None:
        continue

    if post_type.text != "post":
        continue


    status = item.find(
        "wp:status",
        ns
    )

    if status is None or status.text != "publish":
        continue



    title_node = item.find("title")

    if title_node is None:
        continue

    title = title_node.text.strip()



    content_node = item.find(
        "content:encoded",
        ns
    )

    content = clean_text(
        content_node.text
        if content_node is not None
        else ""
    )



    date_node = item.find(
        "wp:post_date",
        ns
    )

    if date_node is not None:

        date = date_node.text.replace(
            " ",
            "T"
        )

    else:

        date = "2024-01-01T00:00:00"



    cats = []

    for c in item.findall("category"):

        if c.attrib.get("domain") == "category":

            cats.append(c.text)



    # 判断短篇

    short_type = None

    for c in cats:

        if c in short_map:

            short_type = short_map[c]

            break



    if short_type:

        num = short_counter[short_type]

        short_counter[short_type] += 1


        path = os.path.join(
            OUTPUT,
            "short",
            short_type,
            f"{num:03}.md"
        )


        save_file(
            path,
            title,
            date,
            content
        )


    else:


        books = [
            c for c in cats
            if c not in ignore_categories
        ]


        if not books:

            continue


        book = books[0]


        bid = get_book_id(book)


        folder = os.path.join(
            OUTPUT,
            "serial",
            bid
        )


        os.makedirs(
            folder,
            exist_ok=True
        )


        chapters = [
            f for f in os.listdir(folder)
            if f.endswith(".md")
            and f != "_index.md"
        ]


        num = len(chapters) + 1


        save_file(
            os.path.join(
                folder,
                f"{num:03}.md"
            ),
            title,
            date,
            content
        )



# 生成小说目录

for bid, title in book_titles.items():

    save_book_index(
        os.path.join(
            OUTPUT,
            "serial",
            bid
        ),
        title
    )



print("转换完成")
print()
print("书籍编号:")

for k,v in book_titles.items():

    print(
        k,
        "=",
        v
    )