"""
parse_trace.py  ── 属于 skills/triaging-e2e-failures/scripts/
--------------------------------------------------------------
Step 1（确定性解析）：解压 Playwright trace.zip → 结构化 JSON + 文本摘要。

Playwright trace.zip 内部结构（v8 格式）：
  - trace.trace   / 0-trace.trace   : 主事件流 (NDJSON)
  - trace.network / 0-trace.network : 网络请求 (NDJSON)
  - trace.stacks                    : 调用栈（JSON）
  - resources/                      : 截图、源码等

事件字段说明（v8 格式）：
  before 事件: {"type":"before", "callId":"call@91", "class":"Frame",
               "method":"click", "params":{...}, "beforeSnapshot":"before@call@91"}
  after  事件: {"type":"after",  "callId":"call@91", "endTime":...,
               "error":{...}, "afterSnapshot":"after@call@91"}
  frame-snapshot 事件: {"type":"frame-snapshot",
                        "snapshot":{"snapshotName":"before@call@91",
                                    "frameUrl":"...", "html":[...]}}

本模块只依赖 Python 标准库。
"""
from __future__ import annotations

import json
import re
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
    api_name: str = ""  # e.g. "frame.click", "page.goto"
    selector: str = ""  # 人类可读的 selector（已从 internal: 格式转换）
    selector_raw: str = ""  # Playwright 原始 internal: 格式
    url: str = ""  # page.goto / frame.goto 的目标 URL
    start_time: float = 0.0
    end_time: float = 0.0
    error: str | None = None
    stack_top: str | None = None
    before_snapshot: str = ""  # 关联的 frame-snapshot 名称
    after_snapshot: str = ""


@dataclass
class ParsedTrace:
    """trace.zip 完整解析结果"""

    trace_path: str = ""
    total_actions: int = 0
    current_page_url: str = ""
    failed_action: TraceAction | None = None
    actions_before_failure: list[TraceAction] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    network_failures: list[dict[str, Any]] = field(default_factory=list)
    dom_testids: list[dict[str, str]] = field(default_factory=list)  # 失败前页面所有 data-testid
    dom_snapshot_found: bool = False  # 是否找到快照（即使 testids 为空也为 True）
    dom_snapshot_excerpt: str | None = None  # 保留兼容
    assertion_detail: dict[str, str] = field(default_factory=dict)  # AssertionError 的 expected/actual

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


def _parse_selector(raw: str) -> str:
    """
    将 Playwright internal: 格式的 selector 转换为人类可读形式。

    例：
      internal:testid=[data-testid="btn-edit"s]  → [data-testid="btn-edit"]
      internal:role=button[name="Submit"l]       → role=button[name="Submit"]
      internal:text="Submit"                     → text="Submit"
    """
    if not raw or not raw.startswith("internal:"):
        return raw

    # testid: internal:testid=[data-testid="xxx"s]
    m = re.search(r'data-testid="([^"]+)"', raw)
    if m:
        return f'[data-testid="{m.group(1)}"]'

    # 去掉 internal: 前缀，去掉尾部的 s/l/i 修饰符
    readable = raw[len("internal:"):]
    readable = re.sub(r'(["\]])[sliSLI](\]|$)', r'\1\2', readable)
    return readable


def _is_truly_full_snapshot(html: Any) -> bool:
    """
    判断 frame-snapshot 的 html 字段是否是真正的完整快照。

    Playwright 存在两种 delta 需要过滤：
    - 纯 delta：html = [[1, 79]] （html[0] 是整数）
    - 半 delta：html = ["HTML", {attrs}, [2,33], ...] （根节点真实，但直接子节点是整数引用）
    """
    if not isinstance(html, list) or not html:
        return False
    if not isinstance(html[0], str):
        return False
    for child in html[2:]:
        if isinstance(child, list) and len(child) >= 1 and isinstance(child[0], int):
            return False
    return True


def _build_api_name(ev: dict[str, Any]) -> str:
    """从 before 事件的 class + method 构造 api_name（v8 格式）。"""
    cls = ev.get("class", "")
    method = ev.get("method", "")
    # 旧格式兼容
    if not cls:
        return ev.get("apiName", "")
    return f"{cls.lower()}.{method}" if method else cls.lower()


def _is_locator_action(api_name: str) -> bool:
    locator_classes = ("locator", "frame", "page", "elementhandle")
    locator_methods = ("click", "fill", "wait_for", "check", "hover",
                       "type", "press", "select_option", "dispatch_event",
                       "inner_text", "inner_html", "text_content", "get_attribute")
    parts = api_name.lower().split(".")
    cls = parts[0] if parts else ""
    method = parts[1] if len(parts) > 1 else ""
    return cls in locator_classes and any(m in method for m in locator_methods)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_trace(trace_path: str | Path, context_window: int = 10) -> ParsedTrace:
    trace_path = Path(trace_path)
    result = ParsedTrace(trace_path=str(trace_path))

    with zipfile.ZipFile(trace_path) as zf:
        # ── 读取事件流 ────────────────────────────────────────────────────
        trace_events: list[dict[str, Any]] = []
        for candidate in ("trace.trace", "0-trace.trace"):
            trace_events.extend(_read_ndjson(zf, candidate))

        network_events: list[dict[str, Any]] = []
        for candidate in ("trace.network", "0-trace.network"):
            network_events.extend(_read_ndjson(zf, candidate))

        # ── 收集 frame-snapshot（完整快照）────────────────
        full_snapshots: dict[str, dict[str, Any]] = {}
        for ev in trace_events:
            if ev.get("type") == "frame-snapshot":
                snap = ev.get("snapshot", {})
                name = snap.get("snapshotName", "")
                html = snap.get("html", [])
                if name and _is_truly_full_snapshot(html):
                    full_snapshots[name] = snap

        # ── 收集 actions（before/after 配对）────────────────────────────
        actions_by_id: dict[str, TraceAction] = {}
        order: list[str] = []

        for ev in trace_events:
            t = ev.get("type")
            cid = ev.get("callId") or ev.get("id") or ""

            if t == "before":
                params = ev.get("params") or {}
                api_name = _build_api_name(ev)

                raw_selector = ""
                url = ""
                if isinstance(params, dict):
                    raw_selector = params.get("selector", "")
                    url = params.get("url", "")

                a = TraceAction(
                    action_id=cid,
                    api_name=api_name,
                    selector=_parse_selector(raw_selector),
                    selector_raw=raw_selector,
                    url=url,
                    start_time=float(ev.get("startTime") or 0),
                    before_snapshot=ev.get("beforeSnapshot", ""),
                )
                actions_by_id[cid] = a
                order.append(cid)

            elif t == "after":
                a = actions_by_id.get(cid)
                if a is None:
                    continue
                a.end_time = float(ev.get("endTime") or 0)
                a.after_snapshot = ev.get("afterSnapshot", "")
                err = ev.get("error")
                if err:
                    a.error = err.get("message") if isinstance(err, dict) else str(err)

            elif t == "console":
                msg_type = ev.get("messageType") or ev.get("type", "")
                if msg_type == "error":
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

    return result


def build_summary(parsed: ParsedTrace, include_dom: bool | None = None,
                  max_context: int = 10) -> str:
    """
    生成 AI 友好的文本摘要（供 Step 2/3/4 推理）。

    include_dom:
      None（默认）= 智能模式：失败 action 为 locator 类时自动附加 data-testid 元素表
      True        = 强制附加
      False       = 强制不附加
    """
    lines: list[str] = [
        f"📁 trace 文件 : {parsed.trace_path}",
        f"📊 总 action 数: {parsed.total_actions}",
    ]

    if parsed.current_page_url:
        lines.append(f"🌍 当前页面 URL : {parsed.current_page_url}")

    # ── 失败 action ──────────────────────────────────────────────────────
    if parsed.failed_action:
        fa = parsed.failed_action
        lines += ["", "❌ [失败 ACTION]", f"   api_name  : {fa.api_name}"]
        if fa.selector:
            lines.append(f"   selector  : {fa.selector}")
        if fa.url:
            lines.append(f"   url       : {fa.url}")
        lines.append(f"   error     : {fa.error}")
        if fa.stack_top:
            lines.append(f"   stack_top : {fa.stack_top}")
    else:
        lines += ["", "⚠️  未检测到明确失败 action"]

    # ── AssertionError 断言 diff（高置信度分类关键证据）────────────────────
    if parsed.assertion_detail:
        lines += ["", "🔎 [断言差异 (AssertionError)]"]
        if "expected" in parsed.assertion_detail:
            lines.append(f'   期望值 (expected) : "{parsed.assertion_detail["expected"]}"')
        if "actual" in parsed.assertion_detail:
            lines.append(f'   实际值 (actual)   : "{parsed.assertion_detail["actual"]}"')

    # ── 失败前 actions ────────────────────────────────────────────────────
    context_actions = parsed.actions_before_failure[-max_context:]
    if context_actions:
        lines += ["", f"🔁 [失败前最后 {len(context_actions)} 个 actions]"]
        for a in context_actions:
            parts = [f"   · {a.api_name}"]
            if a.url:
                parts.append(f"url={a.url!r}")
            if a.selector:
                parts.append(f"selector={a.selector!r}")
            lines.append(" — ".join(parts))

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

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(
        description="Step 1：解析 Playwright trace.zip → 结构化 JSON / 文本摘要"
    )
    ap.add_argument("trace", help="trace.zip 路径")
    dom_group = ap.add_mutually_exclusive_group()
    dom_group.add_argument("--dom", action="store_true", help="强制附加 data-testid 元素表")
    dom_group.add_argument("--no-dom", action="store_true", help="强制不附加")
    ap.add_argument("--json", dest="as_json", action="store_true", help="输出完整 JSON")
    ap.add_argument("--out", default=None, help="保存到文件（默认 stdout）")
    args = ap.parse_args()

    result = parse_trace(args.trace)

    if args.as_json:
        output = result.to_json()
    else:
        flag: bool | None = True if args.dom else (False if args.no_dom else None)
        output = build_summary(result, include_dom=flag)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"✅ 已保存到: {args.out}")
    else:
        print(output)

    sys.exit(0)
