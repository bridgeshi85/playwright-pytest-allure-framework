#!/usr/bin/env python3
"""
diff_parser.py - 解析 unified diff，提取前端变更的结构化信息。

输出 change_manifest.json，供 pr-test-analyzer skill 消费。

用法：
    python diff_parser.py --diff-file pr.diff [--frontend-root auto|path]
    cat pr.diff | python diff_parser.py --frontend-root auto
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ─── 数据模型 ───────────────────────────────────────────────────────────────

@dataclass
class ChangedFile:
    path: str
    change_type: str  # added | modified | deleted | renamed
    additions: int = 0
    deletions: int = 0


@dataclass
class ChangedComponent:
    name: str
    file: str
    change_type: str  # added | modified | deleted


@dataclass
class ChangedFunction:
    file: str
    name: str
    change_type: str  # added | modified | deleted
    line_start: int = 0


@dataclass
class AffectedRoute:
    path: str
    file: str
    change: str  # description of what changed


@dataclass
class AffectedUIElement:
    component: str
    element_type: str  # testid | placeholder | aria-label | role
    value: str
    change: str  # added | modified | deleted


@dataclass
class ChangeManifest:
    pr_number: Optional[int] = None
    base_branch: str = "main"
    frontend_root: str = ""
    is_fork: bool = False
    changed_files: list = field(default_factory=list)
    changed_components: list = field(default_factory=list)
    changed_functions: list = field(default_factory=list)
    affected_routes: list = field(default_factory=list)
    affected_ui_elements: list = field(default_factory=list)
    impact_summary: str = ""


# ─── 前端文件扩展名 ─────────────────────────────────────────────────────────

FRONTEND_EXTENSIONS = {
    ".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte",
    ".css", ".scss", ".less", ".html",
}

# 排除的目录/文件模式
EXCLUDE_PATTERNS = {
    "node_modules", ".git", "dist", "build", ".next", ".nuxt",
    "__tests__", "__mocks__", "coverage", ".cache",
}


# ─── Diff 解析 ──────────────────────────────────────────────────────────────

def parse_diff_header(line: str) -> Optional[tuple[str, str]]:
    """
    解析 diff --git a/path b/path 行。
    返回 (old_path, new_path) 或 None。
    """
    match = re.match(r"^diff --git a/(.+?) b/(.+)$", line)
    if match:
        return match.group(1), match.group(2)
    return None


def parse_hunk_header(line: str) -> Optional[tuple[int, int]]:
    """
    解析 @@ -old_start,old_count +new_start,new_count @@ 行。
    返回 (new_start, new_count) 或 None。
    """
    match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
    if match:
        start = int(match.group(1))
        count = int(match.group(2)) if match.group(2) else 1
        return start, count
    return None


def is_frontend_file(path: str) -> bool:
    """判断是否为前端文件。"""
    p = Path(path)
    if p.suffix not in FRONTEND_EXTENSIONS:
        return False
    # 排除 node_modules 等
    for part in p.parts:
        if part in EXCLUDE_PATTERNS:
            return False
    return True


def parse_diff(diff_text: str) -> list[dict]:
    """
    解析 unified diff，返回文件变更列表。
    每个元素：{path, old_path, change_type, additions, deletions, hunks}
    hunks: [{start, lines}]
    """
    files = []
    current_file = None
    current_hunk = None

    for line in diff_text.splitlines():
        # 新文件 diff
        if line.startswith("diff --git"):
            if current_file:
                files.append(current_file)
            parsed = parse_diff_header(line)
            if parsed:
                old_path, new_path = parsed
                if old_path == "/dev/null":
                    change_type = "added"
                elif new_path == "/dev/null":
                    change_type = "deleted"
                else:
                    change_type = "modified"
                current_file = {
                    "path": new_path if new_path != "/dev/null" else old_path,
                    "old_path": old_path,
                    "change_type": change_type,
                    "additions": 0,
                    "deletions": 0,
                    "hunks": [],
                }
            continue

        if current_file is None:
            continue

        # 处理 new file mode / deleted file mode 标记
        if line.startswith("new file mode"):
            current_file["change_type"] = "added"
            continue
        if line.startswith("deleted file mode"):
            current_file["change_type"] = "deleted"
            continue

        # --- /dev/null 也标记为 added
        if line.startswith("--- /dev/null"):
            current_file["change_type"] = "added"
            continue

        # Hunk header
        hunk_info = parse_hunk_header(line)
        if hunk_info:
            current_hunk = {"start": hunk_info[0], "lines": []}
            current_file["hunks"].append(current_hunk)
            continue

        # 内容行
        if current_hunk is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current_file["additions"] += 1
                current_hunk["lines"].append(("+", line[1:]))
            elif line.startswith("-") and not line.startswith("---"):
                current_file["deletions"] += 1
                current_hunk["lines"].append(("-", line[1:]))
            elif line.startswith(" "):
                current_hunk["lines"].append((" ", line[1:]))

    if current_file:
        files.append(current_file)

    return files


# ─── 前端项目自动检测 ───────────────────────────────────────────────────────

def detect_frontend_root(diff_files: list[dict], repo_root: Path) -> str:
    """
    自动检测前端项目根目录。

    优先级：
    1. diff 中出现 package.json 的最近公共父目录
    2. 仓库根目录存在 package.json → monorepo 模式，按子目录拆分
    3. 仓库根目录存在框架配置文件 → 根目录即前端项目
    4. 取 diff 中前端文件最多的目录
    """
    # 策略 1: 找 diff 中的 package.json
    pkg_dirs = []
    for f in diff_files:
        if f.get("change_type") == "deleted":
            continue
        p = Path(f["path"])
        if p.name == "package.json":
            pkg_dirs.append(p.parent)

    if pkg_dirs:
        # 取最近公共父目录
        if len(pkg_dirs) == 1:
            return str(pkg_dirs[0]) if str(pkg_dirs[0]) != "." else ""
        # 多个 package.json，取公共父目录
        common = pkg_dirs[0]
        for d in pkg_dirs[1:]:
            while not str(d).startswith(str(common)):
                common = common.parent
                if str(common) == ".":
                    break
        return str(common) if str(common) != "." else ""

    # 策略 2 & 3: 检查仓库根
    if (repo_root / "package.json").exists():
        return ""  # 根目录即前端项目

    framework_configs = [
        "vite.config.*", "next.config.*", "nuxt.config.*",
        "vue.config.*", "svelte.config.*", "angular.json",
    ]
    for pattern in framework_configs:
        if list(repo_root.glob(pattern)):
            return ""

    # 策略 4: 统计 diff 中前端文件最多的目录
    dir_counts: dict[str, int] = {}
    for f in diff_files:
        if is_frontend_file(f["path"]):
            p = Path(f["path"])
            # 取第一级目录
            if len(p.parts) > 1:
                top_dir = p.parts[0]
                dir_counts[top_dir] = dir_counts.get(top_dir, 0) + 1

    if dir_counts:
        return max(dir_counts, key=dir_counts.get)

    return ""


# ─── 组件提取 ───────────────────────────────────────────────────────────────

# React 组件模式
REACT_COMPONENT_PATTERNS = [
    # function ComponentName(
    re.compile(r"function\s+([A-Z][a-zA-Z0-9]*)\s*\("),
    # const ComponentName = (
    re.compile(r"(?:const|let|var)\s+([A-Z][a-zA-Z0-9]*)\s*=\s*(?:\([^)]*\)|[a-zA-Z_])\s*=>"),
    # class ComponentName extends
    re.compile(r"class\s+([A-Z][a-zA-Z0-9]*)\s+extends"),
    # export default function
    re.compile(r"export\s+default\s+function\s+([A-Z][a-zA-Z0-9]*)"),
]

# Vue 组件模式
VUE_COMPONENT_PATTERNS = [
    # defineComponent({ name: 'ComponentName'
    re.compile(r"defineComponent\s*\(\s*\{[^}]*name:\s*['\"]([^'\"]+)['\"]"),
]


def extract_components_from_file(file_path: str, hunks: list[dict]) -> list[ChangedComponent]:
    """从 diff hunk 中提取变更的组件名。"""
    components = []
    seen = set()
    p = Path(file_path)
    ext = p.suffix

    # 收集所有变更行内容
    changed_lines = []
    for hunk in hunks:
        for op, content in hunk["lines"]:
            if op in ("+", "-"):
                changed_lines.append((op, content))

    changed_text = "\n".join(content for _, content in changed_lines)

    # React/JSX/TSX
    if ext in (".tsx", ".jsx", ".ts", ".js"):
        for pattern in REACT_COMPONENT_PATTERNS:
            for match in pattern.finditer(changed_text):
                name = match.group(1)
                if name in seen:
                    continue
                seen.add(name)
                # 判断是新增还是修改
                change_type = "modified"
                for op, content in changed_lines:
                    if op == "+" and pattern.search(content):
                        change_type = "added"
                        break
                components.append(ChangedComponent(
                    name=name,
                    file=file_path,
                    change_type=change_type,
                ))

    # Vue SFC
    elif ext == ".vue":
        # 从文件名推断组件名
        component_name = p.stem
        if component_name[0].isupper():
            seen.add(component_name)
            components.append(ChangedComponent(
                name=component_name,
                file=file_path,
                change_type="modified",
            ))
        # 检查 defineComponent（避免与文件名重复）
        for pattern in VUE_COMPONENT_PATTERNS:
            for match in pattern.finditer(changed_text):
                name = match.group(1)
                if name not in seen:
                    seen.add(name)
                    components.append(ChangedComponent(
                        name=name,
                        file=file_path,
                        change_type="modified",
                    ))

    # Svelte
    elif ext == ".svelte":
        component_name = p.stem
        if component_name[0].isupper() and component_name not in seen:
            seen.add(component_name)
            components.append(ChangedComponent(
                name=component_name,
                file=file_path,
                change_type="modified",
            ))

    return components


# ─── 函数提取 ───────────────────────────────────────────────────────────────

FUNCTION_PATTERNS = [
    # function name(
    re.compile(r"function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\("),
    # const name = (
    re.compile(r"(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:\([^)]*\)|[a-zA-Z_])\s*=>"),
    # const name = function
    re.compile(r"(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*function"),
    # async function name(
    re.compile(r"async\s+function\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\("),
    # method definition in class: methodName(
    re.compile(r"^\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*\{"),
]


def extract_functions_from_file(file_path: str, hunks: list[dict]) -> list[ChangedFunction]:
    """从 diff hunk 中提取变更的函数名。"""
    functions = []
    seen = set()

    for hunk in hunks:
        current_line = hunk["start"]
        for op, content in hunk["lines"]:
            if op in ("+", "-"):
                for pattern in FUNCTION_PATTERNS:
                    match = pattern.search(content)
                    if match:
                        name = match.group(1)
                        # 过滤掉常见非函数名
                        if name in ("if", "for", "while", "switch", "catch", "return", "new"):
                            continue
                        key = (file_path, name)
                        if key not in seen:
                            seen.add(key)
                            change_type = "added" if op == "+" else "modified"
                            functions.append(ChangedFunction(
                                file=file_path,
                                name=name,
                                change_type=change_type,
                                line_start=current_line,
                            ))
            if op != "-":
                current_line += 1

    return functions


# ─── 路由提取 ───────────────────────────────────────────────────────────────

ROUTE_FILE_PATTERNS = [
    "router", "routes", "router.js", "routes.ts", "routes.tsx",
    "App.tsx", "App.jsx", "main.tsx", "main.jsx",
]

ROUTE_PATTERNS = [
    # React Router: path="/xxx"
    re.compile(r"""path\s*[=:]\s*["']([^"']+)["']"""),
    # Vue Router: path: '/xxx'
    re.compile(r"""path:\s*["']([^"']+)["']"""),
]


def extract_routes_from_diff(diff_files: list[dict]) -> list[AffectedRoute]:
    """从路由相关文件的变更中提取受影响的路由。"""
    routes = []
    seen = set()

    for f in diff_files:
        path = Path(f["path"])
        name = path.name.lower()

        # 检查是否是路由配置文件
        is_route_file = any(p.lower() in name for p in ROUTE_FILE_PATTERNS)
        if not is_route_file:
            continue

        # 从 hunk 中提取路由路径
        for hunk in f.get("hunks", []):
            for op, content in hunk["lines"]:
                if op == "+":
                    for pattern in ROUTE_PATTERNS:
                        match = pattern.search(content)
                        if match:
                            route_path = match.group(1)
                            key = (route_path, f["path"])
                            if key not in seen:
                                seen.add(key)
                                routes.append(AffectedRoute(
                                    path=route_path,
                                    file=f["path"],
                                    change="route added or modified",
                                ))

    return routes


# ─── UI 元素提取 ────────────────────────────────────────────────────────────

UI_ELEMENT_PATTERNS = [
    # data-testid="xxx"
    (re.compile(r"""data-testid\s*[=:]\s*["']([^"']+)["']"""), "testid"),
    # testId="xxx" (React prop)
    (re.compile(r"""testId\s*[=:]\s*["']([^"']+)["']"""), "testid"),
    # placeholder="xxx"
    (re.compile(r"""placeholder\s*[=:]\s*["']([^"']+)["']"""), "placeholder"),
    # aria-label="xxx"
    (re.compile(r"""aria-label\s*[=:]\s*["']([^"']+)["']"""), "aria-label"),
    # role="xxx"
    (re.compile(r"""role\s*[=:]\s*["']([^"']+)["']"""), "role"),
]


def extract_ui_elements_from_file(file_path: str, hunks: list[dict]) -> list[AffectedUIElement]:
    """从 diff hunk 中提取变更的 UI 元素属性。"""
    elements = []
    seen = set()
    p = Path(file_path)

    # 从文件名推断组件名
    component_name = p.stem if p.stem[0:1].isupper() else "Unknown"

    for hunk in hunks:
        for op, content in hunk["lines"]:
            if op in ("+", "-"):
                for pattern, element_type in UI_ELEMENT_PATTERNS:
                    for match in pattern.finditer(content):
                        value = match.group(1)
                        key = (element_type, value)
                        if key not in seen:
                            seen.add(key)
                            change = "added" if op == "+" else "deleted"
                            elements.append(AffectedUIElement(
                                component=component_name,
                                element_type=element_type,
                                value=value,
                                change=change,
                            ))

    return elements


# ─── 摘要生成 ───────────────────────────────────────────────────────────────

def generate_impact_summary(manifest: ChangeManifest) -> str:
    """生成人类可读的变更影响摘要。"""
    parts = []

    # 文件统计
    n_files = len(manifest.changed_files)
    if n_files > 0:
        parts.append(f"共 {n_files} 个文件被修改")

    # 组件
    if manifest.changed_components:
        names = [c.name for c in manifest.changed_components[:5]]
        suffix = " 等" if len(manifest.changed_components) > 5 else ""
        parts.append(f"涉及组件：{', '.join(names)}{suffix}")

    # 路由
    if manifest.affected_routes:
        paths = [r.path for r in manifest.affected_routes[:3]]
        parts.append(f"影响路由：{', '.join(paths)}")

    # UI 元素
    if manifest.affected_ui_elements:
        n_elements = len(manifest.affected_ui_elements)
        parts.append(f"涉及 {n_elements} 个 UI 元素属性变更")

    # 函数
    if manifest.changed_functions:
        n_funcs = len(manifest.changed_functions)
        parts.append(f"{n_funcs} 个函数被修改")

    return "；".join(parts) if parts else "无可识别的前端变更"


# ─── 主流程 ─────────────────────────────────────────────────────────────────

def build_manifest(
    diff_text: str,
    frontend_root: str,
    repo_root: Path,
    pr_number: Optional[int] = None,
    is_fork: bool = False,
) -> ChangeManifest:
    """构建完整的 change manifest。"""
    manifest = ChangeManifest(pr_number=pr_number, is_fork=is_fork)

    # 解析 diff
    diff_files = parse_diff(diff_text)

    # 过滤前端文件
    frontend_files = [f for f in diff_files if is_frontend_file(f["path"])]

    if not frontend_files:
        manifest.impact_summary = "未检测到前端文件变更"
        return manifest

    # 自动检测前端根目录
    if frontend_root == "auto":
        manifest.frontend_root = detect_frontend_root(frontend_files, repo_root)
    else:
        manifest.frontend_root = frontend_root

    # 填充 changed_files
    for f in frontend_files:
        manifest.changed_files.append(ChangedFile(
            path=f["path"],
            change_type=f["change_type"],
            additions=f["additions"],
            deletions=f["deletions"],
        ))

    # 提取组件
    for f in frontend_files:
        components = extract_components_from_file(f["path"], f.get("hunks", []))
        manifest.changed_components.extend(components)

    # 提取函数
    for f in frontend_files:
        functions = extract_functions_from_file(f["path"], f.get("hunks", []))
        manifest.changed_functions.extend(functions)

    # 提取路由
    manifest.affected_routes = extract_routes_from_diff(frontend_files)

    # 提取 UI 元素
    for f in frontend_files:
        elements = extract_ui_elements_from_file(f["path"], f.get("hunks", []))
        manifest.affected_ui_elements.extend(elements)

    # 生成摘要
    manifest.impact_summary = generate_impact_summary(manifest)

    return manifest


def main():
    parser = argparse.ArgumentParser(description="Parse unified diff for frontend changes")
    parser.add_argument("--diff-file", help="Path to diff file (default: stdin)")
    parser.add_argument("--frontend-root", default="auto",
                        help="Frontend project root, or 'auto' to detect (default: auto)")
    parser.add_argument("--repo-root", default=".",
                        help="Repository root directory (default: current dir)")
    parser.add_argument("--pr-number", type=int, help="PR number (optional)")
    parser.add_argument("--is-fork", action="store_true",
                        help="Whether PR is from a fork")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()

    # 读取 diff
    if args.diff_file:
        diff_text = Path(args.diff_file).read_text(encoding="utf-8")
    else:
        diff_text = sys.stdin.read()

    if not diff_text.strip():
        print("Error: empty diff input", file=sys.stderr)
        sys.exit(1)

    repo_root = Path(args.repo_root).resolve()

    # 构建 manifest
    manifest = build_manifest(
        diff_text=diff_text,
        frontend_root=args.frontend_root,
        repo_root=repo_root,
        pr_number=args.pr_number,
        is_fork=args.is_fork,
    )

    # 输出
    output = json.dumps(asdict(manifest), indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Manifest written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
