#!/bin/bash
# run.sh — 自定位入口，无论 skill 装在哪里都能找到 parse_trace.py
# 用法：bash <skill_dir>/run.sh <trace.zip> [--dom] [--json] [--out FILE]

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SKILL_DIR/scripts/parse_trace.py" "$@"
