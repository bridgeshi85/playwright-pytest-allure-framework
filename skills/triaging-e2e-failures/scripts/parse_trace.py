"""
parse_trace.py  ── 属于 skills/triaging-e2e-failures/scripts/
--------------------------------------------------------------
Step 1（确定性解析）：解压 Playwright trace.zip → 结构化 JSON + 文本摘要。

Playwright trace.zip 内部结构（简化）：
  - trace.trace   / 0-trace.trace   : 主事件流 (NDJSON)
  - trace.network / 0-trace.network : 网络请求 (NDJSON)
  - resources/                      : 截图、DOM 快照等

本模块只依赖 Python 标准库，无需任何第三方包。

调用示例
--------
    # 作为模块导入
    from skills.triaging_e2e_failures.scripts.parse_trace import parse_trace, build_summary

    parsed = parse_trace("output/traces/2026-05-26-1/test_login.zip")
    print(build_summary(parsed))          # 交给 AI 做 Step 2/3/4
    print(parsed.to_json(indent=2))       # 或直接操作结构化数据

    # 命令行直接运行
    python parse_trace.py <trace.zip> [--dom] [--json] [--out result.json]
"""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TraceAction:
    """单个 Playwright action 的精简表示"""

    action_id: str = ""
    api_name: str = ""        # e.g. "page.click", "locator.fill"
    selector: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    error: str | None = None  # 非 None 表示该 action 失败
    stack_top: str | None = None  # 用户代码位置（文件:行 函数名）


@dataclass
class ParsedTrace:
    """trace.zip 完整解析结果"""

    trace_path: str = ""
    total_actions: int = 0
    failed_action: TraceAction | None = None
    actions_before_failure: list[TraceAction] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    network_failures: list[dict[str, Any]] = field(default_factory=list)
    dom_snapshot_excerpt: str | None = None
    screenshots: list[str] = field(default_factory=list)  # zip 内部路径

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_ndjson(zf: zipfile.ZipFile, name: str) -> list[dict[str, Any]]:
    if name not in zf.namelist():
        return []
    events: list[dict[str, Any]] = []
    with zf.open(name) as fp:
        for raw_line in fp:
            line = raw_line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_trace(trace_path: str | Path, context_window: int = 10) -> ParsedTrace:
    """
    解析单个 trace.zip，返回 ParsedTrace（结构化 JSON）。

    :param trace_path:     trace.zip 路径
    :param context_window: 失败 action 之前保留的 action 数（供 AI 分析上下文用）
    """
    trace_path = Path(trace_path)
    result = ParsedTrace(trace_path=str(trace_path))

    with zipfile.ZipFile(trace_path) as zf:
        # ── 读取事件流（兼容不同版本文件名）──────────────────────────────
        trace_events: list[dict[str, Any]] = []
        for candidate in ("trace.trace", "0-trace.trace"):
            trace_events.extend(_read_ndjson(zf, candidate))

        network_events: list[dict[str, Any]] = []
        for candidate in ("trace.network", "0-trace.network"):
            network_events.extend(_read_ndjson(zf, candidate))

        # ── 收集 actions（before/after 配对）────────────────────────────
        actions_by_id: dict[str, TraceAction] = {}
        order: list[str] = []

        for ev in trace_events:
            t = ev.get("type")
            cid = ev.get("callId") or ev.get("id") or ""

            if t == "before":
                params = ev.get("params") or {}
                a = TraceAction(
                    action_id=cid,
                    api_name=ev.get("apiName", ""),
                    selector=params.get("selector", "") if isinstance(params, dict) else "",
                    start_time=float(ev.get("startTime") or 0),
                )
                stack = ev.get("stack") or []
                if stack and isinstance(stack[0], dict):
                    top = stack[0]
                    a.stack_top = (
                        f"{top.get('file', '')}:{top.get('line', '')} "
                        f"{top.get('function', '')}"
                    )
                actions_by_id[cid] = a
                order.append(cid)

            elif t == "after":
                a = actions_by_id.get(cid)
                if a is None:
                    continue
                a.end_time = float(ev.get("endTime") or 0)
                err = ev.get("error")
                if err:
                    a.error = err.get("message") if isinstance(err, dict) else str(err)

            elif t == "console":
                if (ev.get("messageType") or ev.get("type")) == "error":
                    result.console_errors.append(ev.get("text", ""))

            elif t == "event" and ev.get("method") == "pageerror":
                result.page_errors.append(json.dumps(ev.get("params", {}))[:500])

        actions_ordered = [actions_by_id[i] for i in order if i in actions_by_id]
        result.total_actions = len(actions_ordered)

        # ── 定位失败 action ──────────────────────────────────────────────
        failed_idx = next(
            (i for i, a in enumerate(actions_ordered) if a.error), None
        )
        if failed_idx is not None:
            result.failed_action = actions_ordered[failed_idx]
            start = max(0, failed_idx - context_window)
            result.actions_before_failure = actions_ordered[start:failed_idx]
        else:
            result.actions_before_failure = actions_ordered[-context_window:]

        # ── 网络失败（4xx / 5xx）────────────────────────────────────────
        for ev in network_events:
            status = ev.get("status") or (ev.get("response") or {}).get("status")
            if isinstance(status, int) and status >= 400:
                result.network_failures.append({
                    "url": ev.get("url") or (ev.get("request") or {}).get("url"),
                    "status": status,
                    "method": ev.get("method") or (ev.get("request") or {}).get("method"),
                })

        # ── 截图（最多 5 张）────────────────────────────────────────────
        result.screenshots = [
            n for n in zf.namelist()
            if n.startswith("resources/") and n.endswith((".jpeg", ".png"))
        ][:5]

        # ── DOM 快照片段（最后一个，截取前 4KB）──────────────────────────
        snapshot_files = [
            n for n in zf.namelist()
            if "snapshot" in n.lower() and n.endswith((".html", ".json"))
        ]
        if snapshot_files:
            try:
                with zf.open(snapshot_files[-1]) as fp:
                    result.dom_snapshot_excerpt = fp.read(4096).decode("utf-8", errors="ignore")
            except Exception:
                pass

    return result


def build_summary(parsed: ParsedTrace, include_dom: bool = False,
                  max_context: int = 10) -> str:
    """
    将 ParsedTrace 转换为人类可读 + AI 友好的文本摘要。

    供 Skill STEP 2（分类）、STEP 3（修复）、STEP 4（报告）推理使用。

    :param parsed:      parse_trace() 的返回值
    :param include_dom: 是否附加 DOM 快照片段（token 较多，默认关闭）
    :param max_context: 失败前最多展示几个 action
    """
    lines: list[str] = [
        f"📁 trace 文件 : {parsed.trace_path}",
        f"📊 总 action 数: {parsed.total_actions}",
    ]

    # ── 失败 action ──────────────────────────────────────────────────────
    if parsed.failed_action:
        fa = parsed.failed_action
        lines += [
            "",
            "❌ [失败 ACTION]",
            f"   api_name  : {fa.api_name}",
            f"   selector  : {fa.selector!r}",
            f"   error     : {fa.error}",
        ]
        if fa.stack_top:
            lines.append(f"   stack_top : {fa.stack_top}")
    else:
        lines += ["", "⚠️  未检测到明确失败 action（可能是断言失败或超时）"]

    # ── 失败前 actions ────────────────────────────────────────────────────
    context_actions = parsed.actions_before_failure[-max_context:]
    if context_actions:
        lines += ["", f"🔁 [失败前最后 {len(context_actions)} 个 actions]"]
        for a in context_actions:
            suffix = f" — selector={a.selector!r}" if a.selector else ""
            lines.append(f"   · {a.api_name}{suffix}")

    # ── Console errors ───────────────────────────────────────────────────
    if parsed.console_errors:
        lines += ["", "🖥  [Console errors]"]
        for e in parsed.console_errors[:10]:
            lines.append(f"   · {e[:300]}")

    # ── Page errors ──────────────────────────────────────────────────────
    if parsed.page_errors:
        lines += ["", "💥 [Page errors]"]
        for e in parsed.page_errors[:5]:
            lines.append(f"   · {e[:300]}")

    # ── Network 4xx/5xx ──────────────────────────────────────────────────
    if parsed.network_failures:
        lines += ["", "🌐 [Network failures (4xx/5xx)]"]
        for nf in parsed.network_failures[:10]:
            lines.append(f"   · {nf.get('method')} {nf.get('status')} {nf.get('url')}")

    # ── 截图路径（trace 内部）────────────────────────────────────────────
    if parsed.screenshots:
        lines += ["", "📸 [截图（trace 内部路径，最多 5 张）]"]
        for s in parsed.screenshots:
            lines.append(f"   · {s}")

    # ── DOM 快照（可选）──────────────────────────────────────────────────
    if include_dom and parsed.dom_snapshot_excerpt:
        lines += ["", "🗂  [DOM 快照片段（前 2KB）]", parsed.dom_snapshot_excerpt[:2048]]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI — python parse_trace.py <trace.zip> [--dom] [--json] [--out FILE]
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Step 1：解析 Playwright trace.zip → 结构化 JSON / 文本摘要")
    ap.add_argument("trace", help="trace.zip 路径")
    ap.add_argument("--dom", action="store_true", help="在摘要中包含 DOM 快照片段")
    ap.add_argument("--json", dest="as_json", action="store_true",
                    help="输出完整 JSON 而非文本摘要")
    ap.add_argument("--out", default=None, help="保存到文件（默认打印到 stdout）")
    args = ap.parse_args()

    result = parse_trace(args.trace)
    output = result.to_json() if args.as_json else build_summary(result, include_dom=args.dom)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"✅ 已保存到: {args.out}")
    else:
        print(output)
    sys.exit(0)

