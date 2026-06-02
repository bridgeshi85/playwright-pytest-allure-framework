# trace_parser.py — 兼容垫片
# 真正的实现已迁移到 skills/triaging-e2e-failures/scripts/parse_trace.py
# 本文件仅做重新导出，保持旧 import 路径不报错。
from pathlib import Path
import importlib.util as _ilu

_skill_path = Path(__file__).parent.parent / "skills" / "triaging-e2e-failures" / "scripts" / "parse_trace.py"
_spec = _ilu.spec_from_file_location("_trace_parser_impl", _skill_path)
_mod = _ilu.module_from_spec(_spec)   # type: ignore[arg-type]
_spec.loader.exec_module(_mod)        # type: ignore[union-attr]

TraceAction = _mod.TraceAction
ParsedTrace = _mod.ParsedTrace
parse_trace = _mod.parse_trace
build_summary = _mod.build_summary

__all__ = ["TraceAction", "ParsedTrace", "parse_trace", "build_summary"]
