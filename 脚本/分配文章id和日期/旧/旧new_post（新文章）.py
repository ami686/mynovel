"""
new_post.py —— 新建文章（只负责算 slug 和 date，不决定存哪）

逻辑：
  1. 递归扫描 content/ 下所有 .md 文件（跳过 _index.md），
     找出已有编号里最大的数字，算出下一个编号
  2. 打印提示：扫描到几篇已有编号文章、新文章编号是多少
  3. 自动打开记事本，弹出一个临时文件，里面已经填好 slug 和当前时间
  4. 你在记事本里写标题和正文，写完自己"另存为"到想要的分类文件夹，
     文件名随便起，不影响 slug（slug 是写在内容里的，不是看文件名）

用法：双击运行，或 python new_post.py
"""

import os
import re
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

# ─── 配置 ───────────────────────────────────────────────
CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")
# ────────────────────────────────────────────────────────


def parse_front_matter(text):
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not match:
        return None, text
    return match.group(1), text[match.end():]


def get_slug(front_matter):
    match = re.search(r'^slug:\s*["\']?(\S+?)["\']?\s*$', front_matter, re.MULTILINE)
    return match.group(1) if match else None


def scan_max_slug(content_dir):
    max_id = 0
    total_with_slug = 0

    for root, dirs, files in os.walk(content_dir):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            if fname == '_index.md':
                continue

            fpath = os.path.join(root, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()

            fm, _ = parse_front_matter(content)
            if fm is None:
                continue

            slug = get_slug(fm)
            if slug:
                total_with_slug += 1
                try:
                    max_id = max(max_id, int(slug))
                except ValueError:
                    pass

    return max_id, total_with_slug


def current_date_string():
    """生成 Hugo 需要的 ISO 格式当前时间，例如 2026-08-06T16:20:15+08:00"""
    now = datetime.now().astimezone()
    s = now.strftime('%Y-%m-%dT%H:%M:%S%z')
    return s[:-2] + ':' + s[-2:]


def main():
    print(f"扫描目录：{CONTENT_DIR}\n")

    if not os.path.isdir(CONTENT_DIR):
        print(f"❌ 找不到目录: {CONTENT_DIR}")
        input("\n按回车键关闭窗口...")
        return

    max_id, total_with_slug = scan_max_slug(CONTENT_DIR)
    next_slug = max_id + 1

    print(f"已扫描到 {total_with_slug} 篇已有编号文章")
    print(f"新文章编号为: {next_slug}\n")

    # 生成临时文件，填好 slug 和 date，title 留空
    content = (
        "---\n"
        'title: ""\n'
        f'slug: "{next_slug}"\n'
        f"date: {current_date_string()}\n"
        "---\n\n"
    )

    tmp_dir = Path(tempfile.gettempdir())
    tmp_path = tmp_dir / f"新文章_{next_slug}.md"
    tmp_path.write_text(content, encoding="utf-8")

    print("即将打开记事本，请填写标题并写正文。")
    print("写完后请「另存为」到你想要的分类文件夹，文件名随意起。\n")
    input("按回车打开记事本...")

    subprocess.call(["notepad.exe", str(tmp_path)])

    print("\n完成。如果你已经另存到目标文件夹，这里可以直接关闭了。")
    input("\n按回车键关闭窗口...")


if __name__ == "__main__":
    main()
