#!/usr/bin/env python3
"""
fix_md_blank_lines.py

自动检查并修复 Markdown 文件中"忘记空行"的问题。

用法一（推荐，拖拽运行，Windows）:
    直接把一个或多个 .md 文件拖到本脚本图标上，松手即可自动处理，
    处理完窗口会停住显示结果，按任意键再关闭。

用法二（命令行）:
    python3 fix_md_blank_lines.py 文章.md          # 直接修改原文件（会先备份成 .bak）
    python3 fix_md_blank_lines.py 文章.md --check  # 只检查，不修改，报告问题行号
    python3 fix_md_blank_lines.py *.md             # 支持批量处理多个文件

原理:
    在 Hugo/Markdown 里，两个段落之间必须有一个空行，否则会被当成
    同一段落甚至同一行渲染。这个脚本会扫描文件，找到"上一行有内容，
    这一行也有内容，但中间没有空行"的地方，自动插入空行。

    脚本会跳过以下情况，避免误伤合法的 Markdown 语法:
    - Front matter (--- 之间的 YAML 元数据)
    - 代码块 (```包裹的部分)
    - 列表项 (- 或 1. 开头的行，允许紧挨着，因为这是列表语法本身)
    - 标题行 (# 开头)
    - 引用块 (> 开头)
    - HTML 标签独占一行的情况 (如 <p>...</p>，也会被当作段落处理)
"""

import sys
import re
import shutil
from pathlib import Path

LIST_ITEM_RE = re.compile(r'^\s*([-*+]|\d+[.)])\s+')
HEADING_RE = re.compile(r'^\s*#{1,6}\s+')
QUOTE_RE = re.compile(r'^\s*>')
CODE_FENCE_RE = re.compile(r'^\s*(```|~~~)')
TABLE_ROW_RE = re.compile(r'^\s*\|')


def is_special_line(line: str) -> bool:
    """判断这一行是否属于'不需要强制空行'的特殊语法行。"""
    stripped = line.strip()
    if stripped == '':
        return True
    if LIST_ITEM_RE.match(line):
        return True
    if HEADING_RE.match(line):
        return True
    if QUOTE_RE.match(line):
        return True
    if TABLE_ROW_RE.match(line):
        return True
    return False


def fix_content(text: str):
    """
    返回 (修复后的文本, 修改行号列表)
    行号列表是原文件中"在这一行前插入了空行"的位置，方便报告。
    """
    lines = text.split('\n')
    result = []
    issues = []

    in_front_matter = False
    front_matter_delim_count = 0
    in_code_block = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 处理 front matter (--- ... ---)
        if i == 0 and stripped == '---':
            in_front_matter = True
            front_matter_delim_count = 1
            result.append(line)
            continue
        if in_front_matter:
            result.append(line)
            if stripped == '---':
                front_matter_delim_count += 1
                if front_matter_delim_count >= 2:
                    in_front_matter = False
            continue

        # 处理代码块，代码块内部一律不动
        if CODE_FENCE_RE.match(line):
            in_code_block = not in_code_block
            result.append(line)
            continue
        if in_code_block:
            result.append(line)
            continue

        # 核心逻辑：如果上一行是"正文内容行"（非空、非特殊语法），
        # 且当前行也是"正文内容行"，中间没空行 -> 插入空行
        if result:
            prev_line = result[-1]
            prev_is_content = prev_line.strip() != '' and not is_special_line(prev_line)
            curr_is_content = stripped != '' and not is_special_line(line)

            if prev_is_content and curr_is_content:
                result.append('')  # 插入空行
                issues.append(i + 1)  # 记录原文件行号（1-based）

        result.append(line)

    return '\n'.join(result), issues


def process_file(path: Path, check_only: bool):
    text = path.read_text(encoding='utf-8')
    fixed, issues = fix_content(text)

    if not issues:
        print(f"✅ {path.name}: 没发现缺空行的问题")
        return

    print(f"⚠️  {path.name}: 发现 {len(issues)} 处缺空行")
    print(f"   原文件行号: {', '.join(str(n) for n in issues)}")

    if check_only:
        print("   (仅检查模式，未修改文件)")
        return

    backup_path = path.with_suffix(path.suffix + '.bak')
    shutil.copy2(path, backup_path)
    path.write_text(fixed, encoding='utf-8')
    print(f"   已自动修复，原文件备份为 {backup_path.name}")


def main():
    if len(sys.argv) < 2:
        # 没有拖拽任何文件，直接双击运行的情况
        print("=" * 50)
        print("请把一个或多个 .md 文件拖到本脚本图标上运行")
        print("（不是双击打开本脚本，而是拖动 .md 文件到它上面）")
        print("=" * 50)
        input("\n按回车键关闭窗口...")
        return

    args = sys.argv[1:]
    check_only = '--check' in args
    files = [a for a in args if a != '--check']

    if not files:
        print("请提供至少一个 .md 文件路径")
        input("\n按回车键关闭窗口...")
        return

    for f in files:
        path = Path(f)
        if not path.exists():
            print(f"❌ 找不到文件: {f}")
            continue
        if path.suffix.lower() != '.md':
            print(f"⚠️  跳过非 .md 文件: {f}")
            continue
        process_file(path, check_only)

    # 处理完暂停，等用户看完结果再手动关闭窗口
    input("\n处理完成，按回车键关闭窗口...")


if __name__ == '__main__':
    main()
