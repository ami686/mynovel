#!/usr/bin/env python3
"""
检查 Hugo content 目录下是否存在重名文件夹（不区分层级深度）。
用法: python check_dup_folders.py [content目录路径，默认为 ./content]
"""

import os
import sys
from collections import defaultdict

def check_duplicate_folders(root_dir):
    name_to_paths = defaultdict(list)

    for dirpath, dirnames, _ in os.walk(root_dir):
        # 跳过隐藏目录，比如 .git
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for d in dirnames:
            full_path = os.path.join(dirpath, d)
            name_to_paths[d].append(full_path)

    duplicates = {name: paths for name, paths in name_to_paths.items() if len(paths) > 1}

    if not duplicates:
        print("没有发现重名文件夹，所有分类名唯一。")
        return

    print(f"发现 {len(duplicates)} 组重名文件夹：\n")
    for name, paths in sorted(duplicates.items()):
        print(f"文件夹名: [{name}]  (重复 {len(paths)} 次)")
        for p in paths:
            print(f"    - {p}")
        print()

if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "content"
    if not os.path.isdir(root):
        print(f"目录不存在: {root}")
        sys.exit(1)
    check_duplicate_folders(root)
