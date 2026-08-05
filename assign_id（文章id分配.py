"""
Hugo 文章自动分配数字 ID 脚本
- 递归扫描 content/ 下所有 .md 文件
- 跳过 _index.md（分类页）
- 跳过已有 slug 的文章（绝不修改已有编号）
- 没有 slug 的按日期从旧到新排序，分配递增编号写入 front matter
用法：python assign_id.py
"""

import os
import re
from datetime import datetime

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


def get_date(front_matter):
    match = re.search(r'^date:\s*["\']?(.+?)["\']?\s*$', front_matter, re.MULTILINE)
    if not match:
        return datetime.min
    date_str = match.group(1).strip()
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str[:19], fmt)
        except ValueError:
            continue
    return datetime.min


def get_title(front_matter):
    match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', front_matter, re.MULTILINE)
    return match.group(1).strip() if match else "（无标题）"


def insert_slug(front_matter, slug):
    new_line = f'slug: "{slug}"'
    if re.search(r'^title:', front_matter, re.MULTILINE):
        return re.sub(r'(^title:.*$)', r'\1\n' + new_line, front_matter, count=1, flags=re.MULTILINE)
    lines = front_matter.split('\n')
    lines.insert(1, new_line)
    return '\n'.join(lines)


def scan_articles(content_dir):
    max_id = 0
    no_slug = []      # [(date, filepath, title)]
    has_slug = []     # [(slug, filepath, title)] 已有编号的文章

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
            title = get_title(fm)

            if slug:
                has_slug.append((slug, fpath, title))
                try:
                    max_id = max(max_id, int(slug))
                except ValueError:
                    pass
            else:
                date = get_date(fm)
                no_slug.append((date, fpath, title))

    no_slug.sort(key=lambda x: x[0])
    return max_id, has_slug, no_slug


def assign_ids(content_dir):
    print(f"扫描目录：{content_dir}\n")
    max_id, has_slug_files, no_slug_files = scan_articles(content_dir)

    # ── 已有编号的文章只显示数量，不逐条列出 ──
    if has_slug_files:
        print(f"已有编号文章：{len(has_slug_files)} 篇，全部跳过不修改\n")

    if not no_slug_files:
        print("✅ 所有文章都已有编号，无需处理")
        input("\n按回车退出...")
        return

    # ── 预览将要分配的编号 ──
    print(f"── 准备分配编号（共 {len(no_slug_files)} 篇）──")
    next_id = max_id + 1
    preview = []
    for date, fpath, title in no_slug_files:
        rel = os.path.relpath(fpath, os.path.dirname(content_dir))
        print(f"  [{next_id}] {title}  ({rel})")
        preview.append((fpath, str(next_id)))
        next_id += 1

    # ── 让用户确认 ──
    print()
    confirm = input("确认写入以上编号？输入 yes 继续，其他任意键取消：").strip().lower()
    if confirm != 'yes':
        print("已取消，文件未做任何修改")
        input("\n按回车退出...")
        return

    # ── 写入 ──
    for fpath, slug in preview:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        fm, body = parse_front_matter(content)
        new_fm = insert_slug(fm, slug)
        new_content = f"---\n{new_fm}\n---\n{body}"
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)

    print(f"\n✅ 完成，共写入 {len(preview)} 个编号（{max_id + 1} ~ {next_id - 1}）")
    input("\n按回车退出...")


if __name__ == "__main__":
    assign_ids(CONTENT_DIR)
