#!/usr/bin/env python3
"""
category_picker.py — Hugo 分类勾选工具（适配 sections[last] permalink 规则）
══════════════════════════════════════════════════════════════════════
背景：
  你的 hugo.toml 里配了：
    [[permalinks]]
      pattern = '/c/:sections[last]/'
      [permalinks.target]
        kind = 'section'
  这意味着无论分类嵌套多少层，最终 URL 只取"最后一级文件夹名"。
  所以 also_in 字段实际要匹配的，就是目标分类的最后一级文件夹名，
  不是完整路径，也不是中文标题。

用途：
  扫描 content/ 目录下所有分类（含 _index.md 的文件夹），
  用编号勾选的方式为文章设置 also_in，不用手打、不用记 URL 规则。

  同时会检测"同名叶子文件夹"冲突（不同父目录下出现相同的最后一级
  文件夹名，会导致 URL 撞车），提前给出警告。

用法：
  python category_picker.py --add content/serial/a/my-article.md
  python category_picker.py --list          # 只看所有分类和检测冲突
  python category_picker.py --help
══════════════════════════════════════════════════════════════════════
"""

import sys
import textwrap
from pathlib import Path
from collections import defaultdict

try:
    import frontmatter
except ImportError:
    import subprocess
    print("📦 安装依赖 python-frontmatter ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "python-frontmatter", "-q",
                           "--break-system-packages"])
    import frontmatter

ALSO_IN_KEY = "also_in"

# ── 找项目根目录（向上找 hugo.toml/yaml） ─────────────────────────────────────

def find_project_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        for f in ("hugo.toml", "hugo.yaml", "hugo.json", "config.toml"):
            if (p / f).exists():
                return p
    return start

# ── 扫描分类（叶子文件夹名 = 实际生效的 URL key） ─────────────────────────────

def scan_categories(content_path: Path) -> list:
    """
    扫描所有含 _index.md 的分类文件夹。
    返回 [{"slug": 叶子文件夹名, "title": 标题, "path": 完整相对路径}, ...]
    slug 就是 sections[last] 规则下实际生效的 also_in 匹配值。
    """
    results = []
    for idx in sorted(content_path.rglob("_index.md")):
        folder = idx.parent
        if folder == content_path:
            continue  # 跳过 content 根目录本身
        try:
            post = frontmatter.load(idx)
            title = post.get("title", folder.name)
        except Exception:
            title = folder.name

        rel_path = folder.relative_to(content_path).as_posix()
        results.append({
            "slug":  folder.name,     # sections[last] 实际使用的值
            "title": str(title),
            "path":  rel_path,        # 完整路径，仅用于显示区分同名
        })
    return results


def find_slug_collisions(categories: list) -> dict:
    """检测同名叶子文件夹（会导致 URL 撞车）"""
    by_slug = defaultdict(list)
    for c in categories:
        by_slug[c["slug"]].append(c["path"])

    return {slug: paths for slug, paths in by_slug.items() if len(paths) > 1}

# ── 命令：列出分类 + 冲突检测 ──────────────────────────────────────────────────

def cmd_list(project_root: Path):
    content_path = project_root / "content"
    if not content_path.exists():
        sys.exit(f"❌ 未找到 content 目录: {content_path}")

    cats = scan_categories(content_path)
    if not cats:
        print("ℹ️  未找到任何分类（_index.md）。")
        return

    print(f"\n📂 找到 {len(cats)} 个分类\n")
    for c in cats:
        print(f"  [{c['slug']:<12}] {c['title']:<10}  (content/{c['path']}/)")

    collisions = find_slug_collisions(cats)
    if collisions:
        print(f"\n⚠️  发现 {len(collisions)} 组同名叶子文件夹，会导致 URL 撞车：\n")
        for slug, paths in collisions.items():
            print(f"  \"{slug}\" 同时出现在：")
            for p in paths:
                print(f"    - content/{p}/")
        print("\n  建议给其中一个改名，否则 Hugo 构建时可能报重复输出路径错误，")
        print("  或者两个分类会意外共享同一篇跨挂文章。")
    else:
        print("\n✅ 没有发现同名叶子文件夹冲突。")
    print()

# ── 交互勾选 ─────────────────────────────────────────────────────────────────

def pick_loop(cats: list, selected: set) -> set | None:
    while True:
        print("\n┌─ 可选分类 " + "─" * 46)
        for i, c in enumerate(cats, 1):
            mark = "●" if c["slug"] in selected else "○"
            print(f"│  [{i:2d}] {mark}  {c['title']:<10}  ({c['path']})")
        print("└" + "─" * 57)

        if selected:
            names = [c["title"] for c in cats if c["slug"] in selected]
            print(f"  已选：{', '.join(names)}")
        else:
            print("  已选：（无）")

        print("\n  输入编号切换（空格/逗号分隔），回车确认，q 取消")
        raw = input("\n> ").strip()

        if raw.lower() == "q":
            return None
        if not raw:
            return selected

        for token in raw.replace(",", " ").split():
            if token.isdigit():
                idx = int(token) - 1
                if 0 <= idx < len(cats):
                    slug = cats[idx]["slug"]
                    if slug in selected:
                        selected.discard(slug)
                    else:
                        selected.add(slug)
                else:
                    print(f"  ⚠️  编号 {token} 超出范围")
            else:
                print(f"  ⚠️  无法识别：{token}")

# ── 命令：为文章选分类 ────────────────────────────────────────────────────────

def cmd_add(project_root: Path, article_path: str):
    ap = Path(article_path).resolve()
    if not ap.exists():
        sys.exit(f"❌ 文件不存在: {ap}")

    content_path = project_root / "content"
    cats = scan_categories(content_path)

    if not cats:
        sys.exit("❌ content 目录下没有找到任何分类（_index.md）。")

    collisions = find_slug_collisions(cats)
    if collisions:
        print(f"⚠️  注意：有 {len(collisions)} 组分类叶子文件夹重名，可能导致选择歧义，"
              f"建议先跑 --list 查看详情。\n")

    try:
        post = frontmatter.load(ap)
    except Exception as e:
        sys.exit(f"❌ 无法解析 frontmatter: {e}")

    current_raw = post.get(ALSO_IN_KEY, [])
    if isinstance(current_raw, str):
        current_raw = [current_raw]
    selected = {str(c).strip() for c in current_raw}

    # 排除文章自己所在的那个叶子分类（没必要跨挂自己）
    own_slug = ap.parent.name
    pick_list = [c for c in cats if c["slug"] != own_slug]

    title = post.get("title", ap.stem)
    try:
        rel = ap.relative_to(project_root)
    except ValueError:
        rel = ap
    print(f"\n📄 {rel}  [{title}]")
    print(f"   主分类文件夹：{own_slug}（自动生效，不需要勾选）\n")

    result = pick_loop(pick_list, set(selected))

    if result is None:
        print("已取消，文件未修改。")
        return

    final = sorted(result)
    post[ALSO_IN_KEY] = final
    ap.write_text(frontmatter.dumps(post), "utf-8")

    print()
    if final:
        print(f"✅ 已写入 also_in：")
        for slug in final:
            match = next((c for c in cats if c["slug"] == slug), None)
            label = match["title"] if match else slug
            print(f"   {slug}  ({label})")
    else:
        print("✅ 已清空 also_in。")

# ── 帮助 ──────────────────────────────────────────────────────────────────────

HELP = textwrap.dedent("""
    category_picker.py — 分类勾选工具
    ════════════════════════════════════
    用法：
      python category_picker.py --add 文章路径     交互勾选分类
      python category_picker.py --list             查看所有分类 + 冲突检测
      python category_picker.py --help             显示帮助

    示例：
      python category_picker.py --add content/serial/a/my-article.md
""")

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(HELP)
        sys.exit(0)

    project_root = find_project_root(Path.cwd())

    if "--list" in args:
        cmd_list(project_root)
    elif "--add" in args:
        idx = args.index("--add")
        if idx + 1 >= len(args):
            sys.exit("❌ --add 需要指定文章路径")
        cmd_add(project_root, args[idx + 1])
    else:
        print(HELP)
