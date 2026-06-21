#!/usr/bin/env python3
"""
extract_dom.py
去除 <style>/<script> 标签，只保留可读的 DOM 结构（保留 data-testid）。

用法:
    python extract_dom.py <html_file>
    python extract_dom.py output/screenshots/2026-06-08-3/test_profile_edit_button_not_found.html
"""

import argparse
import re
import sys
from pathlib import Path


def extract_root(html_text: str) -> str:
    """提取 #root div 的内容（或 <body> fallback），去除 style/script 噪音。"""
    # 去除所有 <style ...>...</style>
    html_text = re.sub(r"<style[^>]*>.*?</style>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    # 去除所有 <script ...>...</script>
    html_text = re.sub(r"<script[^>]*>.*?</script>", "", html_text, flags=re.DOTALL | re.IGNORECASE)

    # 尝试提取 <div id="root">...</div>
    root_match = re.search(r'(<div[^>]+id=["\']root["\'][^>]*>)(.*?)(</div>\s*$)', html_text, re.DOTALL | re.IGNORECASE)
    if root_match:
        content = root_match.group(0)
    else:
        # fallback: 提取 <body>...</body>
        body_match = re.search(r"<body[^>]*>(.*?)</body>", html_text, re.DOTALL | re.IGNORECASE)
        content = body_match.group(0) if body_match else html_text.strip()

    # 压缩连续空白行
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def main():
    parser = argparse.ArgumentParser(description="从 page.content() HTML 提取 #root DOM 内容")
    parser.add_argument("html_file", help="HTML 文件路径")
    parser.add_argument("--out", help="输出文件（默认 stdout）")
    args = parser.parse_args()

    path = Path(args.html_file)
    if not path.exists():
        print(f"[ERROR] 文件不存在: {path}", file=sys.stderr)
        sys.exit(1)

    html_text = path.read_text(encoding="utf-8", errors="replace")
    result = extract_root(html_text)

    if args.out:
        Path(args.out).write_text(result, encoding="utf-8")
        print(f"[OK] 已写入 {args.out}（{len(result)} 字节）")
    else:
        print(result)


if __name__ == "__main__":
    main()
