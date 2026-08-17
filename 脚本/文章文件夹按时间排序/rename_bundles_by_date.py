#!/usr/bin/env python3
"""
按 index.md front matter 里的 date 字段，把某个分类目录下的
Hugo page bundle 文件夹重命名为 1, 2, 3 ...（最早发布 = 1）

用法：
    python3 rename_bundles_by_date.py /path/to/content/分类目录 [--dry-run]
"""

import sys
import re
import shutil
from pathlib import Path

try:
    import yaml
except ImportError:
    print("需要 PyYAML，请先执行: pip install pyyaml --break-system-packages")
    sys.exit(1)


def find_index_file(bundle_dir: Path):
    """找到 bundle 里的 index.md / index.<lang>.md"""
    candidates = sorted(bundle_dir.glob("index*.md"))
    return candidates[0] if candidates else None


def parse_date(index_file: Path):
    text = index_file.read_text(encoding="utf-8")

    # YAML front matter: --- ... ---
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if m:
        data = yaml.safe_load(m.group(1)) or {}
        return data.get("date")

    # TOML front matter: +++ ... +++
    m = re.match(r"^\+\+\+\s*\n(.*?)\n\+\+\+\s*\n", text, re.DOTALL)
    if m:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        data = tomllib.loads(m.group(1))
        return data.get("date")

    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv

    if not args:
        print("用法: python3 rename_bundles_by_date.py /path/to/content/分类目录 [--dry-run]")
        sys.exit(1)

    root = Path(args[0]).resolve()
    if not root.is_dir():
        print(f"目录不存在: {root}")
        sys.exit(1)

    bundles = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        index_file = find_index_file(child)
        if not index_file:
            print(f"跳过（没有 index.md）: {child.name}")
            continue
        date = parse_date(index_file)
        if date is None:
            print(f"跳过（front matter 没有 date 字段）: {child.name}")
            continue
        bundles.append((child, date))

    if not bundles:
        print("没有找到任何带 date 的 page bundle。")
        return

    # 按时间升序排序，最早发布的排第一
    bundles.sort(key=lambda x: str(x[1]))

    print("排序结果（最早 -> 最新）：")
    for i, (folder, date) in enumerate(bundles, start=1):
        print(f"  {i}. {folder.name}  (date={date})")

    if dry_run:
        print("\n[dry-run] 未实际重命名，去掉 --dry-run 参数以真正执行。")
        return

    import time

    def safe_rename(src: Path, dst: Path, retries=5, delay=1.0):
        """带重试的重命名，避免文件被占用时直接崩溃"""
        last_err = None
        for attempt in range(retries):
            try:
                src.rename(dst)
                return
            except PermissionError as e:
                last_err = e
                print(f"  文件被占用，{delay}秒后重试... ({attempt + 1}/{retries})")
                time.sleep(delay)
        raise last_err

    # 第一步：全部改成临时名，避免和目标数字名冲突
    # 如果中途失败，自动把已经改名的全部退回原名，保证不会半途而废
    temp_paths = []
    try:
        for folder, _ in bundles:
            tmp = folder.with_name(f"_tmp_rename_{folder.name}")
            print(f"改名: {folder.name} -> {tmp.name}")
            safe_rename(folder, tmp)
            temp_paths.append((tmp, folder))
    except Exception as e:
        print(f"\n改名失败: {e}")
        print("正在自动回滚，把已经改的名字退回原样...")
        for tmp, original in reversed(temp_paths):
            try:
                safe_rename(tmp, original)
                print(f"  已还原: {tmp.name} -> {original.name}")
            except Exception as rollback_err:
                print(f"  还原失败，请手动把 {tmp} 改名为 {original.name}: {rollback_err}")
        print("\n回滚完成，所有文件夹已恢复原名，未造成数据丢失。")
        print("请关闭所有打开着该文件夹的窗口/程序后再重试。")
        return

    # 第二步：临时名 -> 最终数字名
    for i, (tmp, _original) in enumerate(temp_paths, start=1):
        final = root / str(i)
        if final.exists():
            print(f"警告：目标文件夹 {final} 已存在，跳过 {tmp.name}")
            continue
        print(f"改名: {tmp.name} -> {i}")
        safe_rename(tmp, final)

    print("\n重命名完成。")
    print("提醒：文件夹名变化会改变默认 URL(slug)，如需保留旧链接，")
    print("请提前在各 index.md 的 front matter 里加上 slug 或 url 字段。")


if __name__ == "__main__":
    main()
