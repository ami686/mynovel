"""
给 serial 下所有层级子目录的 _index.md 的 frontmatter 加上 schema: series
- 不处理 serial/_index.md 本身
- 只处理名为 _index.md 的文件，不碰文章

用法：直接双击运行即可。先预览，输入 y 回车后才会真正写入。
"""
import os
import re
import traceback

ROOT = r"D:\mynovel\content\serial"   # 分类大目录
KEY, VALUE = "schema", "series"


def process(path):
    with open(path, "rb") as f:
        raw = f.read()

    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)

    first = lines[0].strip() if lines else ""
    if first == "---":
        delim, new_line = "---", f"{KEY}: {VALUE}"
        pat = re.compile(rf"^{KEY}\s*:")
    elif first == "+++":
        delim, new_line = "+++", f'{KEY} = "{VALUE}"'
        pat = re.compile(rf"^{KEY}\s*=")
    else:
        lines = ["---", f"{KEY}: {VALUE}", "---"] + lines
        return nl.join(lines), bom, "将新增 frontmatter"

    end = next((i for i in range(1, len(lines)) if lines[i].strip() == delim), None)
    if end is None:
        return None, bom, "frontmatter 没有结束分隔符，跳过"

    for i in range(1, end):
        if pat.match(lines[i]):
            if lines[i].strip() == new_line:
                return None, bom, "已存在，无需修改"
            lines[i] = new_line
            return nl.join(lines), bom, "将更新原有值"

    lines.insert(end, new_line)
    return nl.join(lines), bom, "将添加"


def main():
    if not os.path.isdir(ROOT):
        print(f"目录不存在：{ROOT}")
        return

    print("【预览】以下是将要发生的修改（此时还没有改任何文件）：\n")
    todo = []   # (路径, 新内容, bom)
    total = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames.sort()
        if os.path.normpath(dirpath) == os.path.normpath(ROOT):
            continue  # 跳过 serial 根目录本身
        if "_index.md" not in filenames:
            continue

        idx = os.path.join(dirpath, "_index.md")
        rel = os.path.relpath(dirpath, ROOT)
        new_text, bom, msg = process(idx)
        print(f"[{rel}] {msg}")
        total += 1
        if new_text is not None:
            todo.append((idx, new_text, bom))

    print(f"\n共检查 {total} 个 _index.md，其中 {len(todo)} 个需要修改。")
    if not todo:
        return

    ans = input("确认写入？输入 y 回车确认，直接回车取消：").strip().lower()
    if ans != "y":
        print("已取消，没有修改任何文件。")
        return

    for idx, new_text, bom in todo:
        with open(idx, "wb") as f:
            f.write((b"\xef\xbb\xbf" if bom else b"") + new_text.encode("utf-8"))
    print(f"完成，已修改 {len(todo)} 个文件。")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
    input("\n按回车键退出...")
