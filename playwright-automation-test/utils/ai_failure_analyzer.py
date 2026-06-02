"""
ai_failure_analyzer.py
-----------------------
Playwright E2E 失败日志分析工具

职责：
  Step 1  解析 trace.zip → ParsedTrace（结构化数据）
  Step 1b 生成文本摘要   → build_summary()  供 AI Skill 直接使用

CLI 用法
--------
# 解析并打印文本摘要（粘贴给 AI 或由 Skill 自动调用）
python -m utils.ai_failure_analyzer --trace output/traces/.../test_login.zip

# 同时保存摘要文本和完整 JSON
python -m utils.ai_failure_analyzer \\
    --trace output/traces/.../test_login.zip \\
    --summary-out output/reports/test_login_summary.txt \\
    --json-out   output/reports/test_login_trace.json

# 附加 DOM 快照（token 更多但信息更全）
python -m utils.ai_failure_analyzer --trace ... --dom
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# trace_parser 位于 skills/e2e-failure-analyzer/
# 支持两种调用上下文：直接 python 运行 或 pytest 环境
try:
    from skills.e2e_failure_analyzer.trace_parser import parse_trace, build_summary
except ModuleNotFoundError:
    import importlib.util as _ilu
    _skill_path = (
        Path(__file__).parent.parent
        / "skills" / "e2e-failure-analyzer" / "trace_parser.py"
    )
    _spec = _ilu.spec_from_file_location("trace_parser", _skill_path)
    _mod = _ilu.module_from_spec(_spec)   # type: ignore[arg-type]
    _spec.loader.exec_module(_mod)        # type: ignore[union-attr]
    parse_trace = _mod.parse_trace        # type: ignore[assignment]
    build_summary = _mod.build_summary    # type: ignore[assignment]


def analyze(trace_path: str | Path,
            include_dom: bool = False,
            json_out: str | Path | None = None,
            summary_out: str | Path | None = None) -> str:
    """
    解析 trace.zip 并返回文本摘要字符串。
    适合在 Skill 或 conftest 中以编程方式调用。

    :param trace_path:  trace.zip 路径
    :param include_dom: 摘要是否附加 DOM 快照片段
    :param json_out:    若指定，同时把完整 JSON 存到该路径
    :param summary_out: 若指定，同时把摘要文本存到该路径
    :return:            文本摘要（交给 AI Skill 完成 Step 2/3/4）
    """
    parsed = parse_trace(trace_path)
    summary = build_summary(parsed, include_dom=include_dom)

    if json_out:
        out = Path(json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(parsed.to_json(), encoding="utf-8")

    if summary_out:
        out = Path(summary_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(summary, encoding="utf-8")

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ai_failure_analyzer",
        description="解析 Playwright trace.zip，生成供 AI Skill 分析的文本摘要",
    )
    p.add_argument("--trace", required=True, metavar="PATH",
                   help="trace.zip 文件路径")
    p.add_argument("--dom", action="store_true",
                   help="在摘要中附加 DOM 快照片段（token 较多）")
    p.add_argument("--summary-out", default=None, metavar="PATH",
                   help="将摘要文本保存到指定文件")
    p.add_argument("--json-out", default=None, metavar="PATH",
                   help="将完整解析 JSON 保存到指定文件")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    print(f"[Step 1] 解析 trace: {args.trace}")
    summary = analyze(
        trace_path=args.trace,
        include_dom=args.dom,
        json_out=args.json_out,
        summary_out=args.summary_out,
    )

    if args.json_out:
        print(f"         JSON 已保存 → {args.json_out}")
    if args.summary_out:
        print(f"         摘要已保存 → {args.summary_out}")

    print()
    print("=" * 64)
    print("▼ Trace 摘要（将此内容交给 AI Skill 完成 Step 2/3/4）")
    print("=" * 64)
    print(summary)
    print("=" * 64)
    print()
    print("💡 下一步：将上方摘要粘贴给 AI，或触发 Skill：")
    print("   '请分析以下 Playwright 失败，给出根因报告'")

    return 0


if __name__ == "__main__":
    sys.exit(main())
