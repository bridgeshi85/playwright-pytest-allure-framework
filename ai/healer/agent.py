"""
ai/healer/agent.py  — Healer Agent (aligned with triaging-e2e-failures Skill)

错误分类规则完全对齐 .claude/skills/triaging-e2e-failures/references/triage_rules.md
修复模式对齐 references/fix_patterns.md
报告格式对齐 assets/report_template.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import anthropic

# ── 常量 ─────────────────────────────────────────────────────────────────────
SKILL_DIR = Path(".claude/skills/triaging-e2e-failures")
PARSE_TRACE = SKILL_DIR / "scripts/parse_trace.py"
EXTRACT_DOM  = SKILL_DIR / "scripts/extract_dom.py"
TRIAGE_RULES = SKILL_DIR / "references/triage_rules.md"
FIX_PATTERNS = SKILL_DIR / "references/fix_patterns.md"
REPORT_TPL   = SKILL_DIR / "assets/report_template.md"

TRACES_DIR      = Path("playwright-automation-test/output/traces")
SCREENSHOTS_DIR = Path("playwright-automation-test/output/screenshots")
LOG_FILE        = Path("playwright-automation-test/output/logs/test.log")

CONFIDENCE_AUTO_FIX   = 0.70   # >= 此值 + flaky_test/selector_renamed → 自动修复
CONFIDENCE_MIN_TRIAGE = 0.50   # < 此值 → 降为 unknown


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: 收集证据
# ─────────────────────────────────────────────────────────────────────────────

def collect_evidence(test_name: str, run_dir: str | None = None) -> dict:
    """
    对应 SKILL.md Step 1：
      1a  枚举 traces 目录
      1b  parse_trace.py  → action 序列 + console errors
      1c  extract_dom.py  → 清洁 DOM
      1d  test.log        → 用例日志片段
    """
    evidence = {
        "test_name": test_name,
        "trace_summary": "",
        "dom_snapshot": "",
        "log_snippet": "",
        "trace_zip": None,
        "html_file": None,
    }

    # ── 1a 找 trace zip ──────────────────────────────────────────────────────
    trace_zip = _find_artifact(TRACES_DIR, test_name, ".zip", run_dir)
    if trace_zip:
        evidence["trace_zip"] = str(trace_zip)
        # ── 1b parse_trace ───────────────────────────────────────────────────
        evidence["trace_summary"] = _run_script(PARSE_TRACE, str(trace_zip))
    else:
        evidence["trace_summary"] = "⚠️ No trace.zip found"

    # ── 1c extract_dom ───────────────────────────────────────────────────────
    html_file = _find_artifact(SCREENSHOTS_DIR, test_name, ".html", run_dir)
    if html_file:
        evidence["html_file"] = str(html_file)
        evidence["dom_snapshot"] = _run_script(EXTRACT_DOM, str(html_file))
    else:
        evidence["dom_snapshot"] = "⚠️ No HTML snapshot found"

    # ── 1d test.log 日志片段 ─────────────────────────────────────────────────
    evidence["log_snippet"] = _extract_log_snippet(test_name)

    return evidence


def _find_artifact(base_dir: Path, test_name: str, ext: str,
                   run_dir: str | None) -> Path | None:
    if not base_dir.exists():
        return None
    subdirs = sorted(base_dir.iterdir(), reverse=True) if run_dir is None \
              else [base_dir / run_dir]
    for subdir in subdirs:
        if not subdir.is_dir():
            continue
        for f in subdir.glob(f"*{ext}"):
            if test_name in f.stem or test_name.replace("test_", "") in f.stem:
                return f
    return None


def _run_script(script: Path, *args: str) -> str:
    if not script.exists():
        return f"⚠️ Script not found: {script}"
    try:
        result = subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout or result.stderr or "⚠️ No output"
    except Exception as e:
        return f"⚠️ Script error: {e}"


def _extract_log_snippet(test_name: str) -> str:
    if not LOG_FILE.exists():
        return "⚠️ test.log not found"
    content = LOG_FILE.read_text(errors="replace")
    pattern = rf"=== TEST START: {re.escape(test_name)} ===(.*?)=== TEST END: {re.escape(test_name)}"
    m = re.search(pattern, content, re.DOTALL)
    if m:
        return m.group(0)[:3000]
    # fallback: grep 最后 50 行含 test_name 的内容
    lines = [l for l in content.splitlines() if test_name in l]
    return "\n".join(lines[-50:]) or "⚠️ No log entry found"


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Claude 根因分类 (对齐 triage_rules.md)
# ─────────────────────────────────────────────────────────────────────────────

def classify_with_claude(client: anthropic.Anthropic, evidence: dict) -> dict:
    """
    对应 SKILL.md Step 2 — 参照 triage_rules.md 分类，输出 JSON。
    """
    rules_text   = TRIAGE_RULES.read_text()   if TRIAGE_RULES.exists()   else ""
    patterns_text = FIX_PATTERNS.read_text()  if FIX_PATTERNS.exists()   else ""

    prompt = f"""你是一个 Playwright E2E 测试失败根因分析专家。

## 分类规则
{rules_text}

## 失败证据

### Trace 摘要
{evidence['trace_summary'][:3000]}

### DOM 快照
{evidence['dom_snapshot'][:2000]}

### 日志片段
{evidence['log_snippet'][:1500]}

---

请严格按以上规则分类，输出纯 JSON（不加 markdown 包裹）：
{{
  "category": "real_bug|flaky_test|flaky_data|unknown",
  "sub_category": "api_failure|selector_renamed|element_missing|delayed_render|data_contamination|data_setup_missing|null",
  "confidence": 0.00,
  "matched_rule": "Rule N",
  "reasoning": "中文说明，≤100字",
  "key_evidence": ["证据1", "证据2"],
  "suggested_fix_selector": "selector or null",
  "fix_pattern": "Pattern N or null",
  "fix_code_before": "原代码片段 or null",
  "fix_code_after": "修复后代码片段 or null"
}}

置信度低于 0.5 时 category 必须是 unknown。"""

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        return {
            "category": "unknown", "sub_category": None,
            "confidence": 0.0, "matched_rule": "N/A",
            "reasoning": raw[:200], "key_evidence": [],
            "suggested_fix_selector": None,
            "fix_pattern": None, "fix_code_before": None, "fix_code_after": None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: 生成报告 (对齐 report_template.md)
# ─────────────────────────────────────────────────────────────────────────────

def generate_report(results: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 🔍 E2E 失败根因汇总报告",
        "",
        f"> 生成时间：{now}  ",
        f"> 分析用例数：{len(results)}",
        "",
        "---",
        "",
        "## 汇总表",
        "",
        "| 用例 | 分类 | 置信度 | 失败原因 | 修复方向 |",
        "|------|------|--------|----------|----------|",
    ]

    for r in results:
        cat    = r.get("category", "unknown")
        subcat = r.get("sub_category") or ""
        conf   = r.get("confidence", 0.0)
        label  = f"`{cat}/{subcat}`" if subcat else f"`{cat}`"
        if conf < 0.6:
            label += "（建议人工复核）"
        conf_str = f"{conf:.2f}"
        reason   = r.get("reasoning", "")[:30]
        fix_dir  = _fix_direction_short(r)
        test     = r["test_name"]
        lines.append(f"| `{test}` | {label} | {conf_str} | {reason} | {fix_dir} |")

    lines += ["", "---", "", "## 逐条详情", ""]

    # 用例数 > 5 时只展示 confidence 最高 + unknown
    show_all = len(results) <= 5
    if not show_all:
        sorted_r = sorted(results, key=lambda x: x.get("confidence", 0), reverse=True)
        to_show  = [sorted_r[0]] + [r for r in results if r.get("category") == "unknown"]
        omitted  = len(results) - len(to_show)
    else:
        to_show = results
        omitted = 0

    for r in to_show:
        lines += _render_detail(r)

    if omitted:
        lines += [
            f"> 其余 {omitted} 条用例已省略。如需查看完整详情，请单独分析对应 trace。",
            "",
        ]

    lines += [
        "---",
        "",
        "*报告由 AI Skill **triaging-e2e-failures** 自动生成 · 置信度 < 0.6 建议人工复核*",
    ]
    return "\n".join(lines)


def _fix_direction_short(r: dict) -> str:
    cat    = r.get("category", "unknown")
    subcat = r.get("sub_category") or ""
    sel    = r.get("suggested_fix_selector")
    if cat == "flaky_test" and subcat == "selector_renamed" and sel:
        return f"替换 selector → `{sel}`"
    if cat == "flaky_test" and subcat == "element_missing":
        return "用 `playwright show-trace` 确认页面内容"
    if cat == "real_bug" and subcat == "api_failure":
        return "排查后端接口，提交缺陷工单"
    if cat == "flaky_data":
        return "检查 fixture 数据清理逻辑"
    return "人工 `playwright show-trace` 排查"


def _render_detail(r: dict) -> list[str]:
    cat    = r.get("category", "unknown")
    subcat = r.get("sub_category") or ""
    conf   = r.get("confidence", 0.0)
    rule   = r.get("matched_rule", "N/A")
    lines  = [
        f"### `{r['test_name']}`",
        "",
        f"- **分类**：`{cat}` / `{subcat}`",
        f"- **置信度**：{conf:.2f}（命中 `{rule}`）",
        f"- **失败原因**：{r.get('reasoning', '')}",
        "- **关键证据**：",
    ]
    for ev in r.get("key_evidence", []):
        lines.append(f"  - `{ev}`")

    lines.append(f"- **修复方向**：{_fix_direction_long(r)}")

    before = r.get("fix_code_before")
    after  = r.get("fix_code_after")
    if before and after:
        lines += [
            "- **修复代码**：",
            "  ```python",
            f"  # ❌ Before",
            *[f"  {l}" for l in before.splitlines()],
            f"  # ✅ After",
            *[f"  {l}" for l in after.splitlines()],
            "  ```",
        ]
    lines += ["", "---", ""]
    return lines


def _fix_direction_long(r: dict) -> str:
    cat    = r.get("category", "unknown")
    subcat = r.get("sub_category") or ""
    sel    = r.get("suggested_fix_selector")
    trace  = r.get("trace_zip", "<trace.zip>")

    if cat == "flaky_test" and subcat == "selector_renamed" and sel:
        return f"将失败 selector 替换为 `{sel}`（来自 DOM 快照匹配）"
    if cat == "flaky_test" and subcat == "element_missing":
        return f"运行 `playwright show-trace {trace}` 确认页面实际内容，检查是否延迟渲染或功能已删除"
    if cat == "real_bug" and subcat == "api_failure":
        return "检查对应后端接口（状态码 4xx/5xx），提交缺陷工单"
    if cat == "flaky_data":
        return "检查 pytest fixture 的数据清理逻辑，确保测试前置条件满足"
    return f"证据不足，建议人工打开 `playwright show-trace {trace}` 排查"


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: 生成 healing-result.json (供 CI 路由决策)
# ─────────────────────────────────────────────────────────────────────────────

def build_healing_result(triage: dict, evidence: dict,
                         report_path: str, repo: str, sha: str) -> dict:
    cat    = triage.get("category", "unknown")
    subcat = triage.get("sub_category") or ""
    conf   = triage.get("confidence", 0.0)

    # 决策：只有 flaky_test/selector_renamed + conf >= 0.7 才自愈
    if cat == "flaky_test" and subcat == "selector_renamed" and conf >= CONFIDENCE_AUTO_FIX:
        status = "healed"
        fixes  = [{
            "file": evidence.get("trace_zip", ""),   # agent.py 回填实际测试文件
            "old_code": triage.get("fix_code_before") or "",
            "new_code": triage.get("fix_code_after") or "",
        }]
    else:
        status = "not_healable"
        fixes  = []

    return {
        "status": status,
        "failed_test": evidence["test_name"],
        "error_category": cat,
        "error_sub_category": subcat,
        "error_category_name": f"{cat}/{subcat}",
        "confidence": conf,
        "matched_rule": triage.get("matched_rule", ""),
        "root_cause": triage.get("reasoning", ""),
        "key_evidence": triage.get("key_evidence", []),
        "recommended_fix": _fix_direction_long(triage),
        "fix_summary": triage.get("suggested_fix_selector") or triage.get("reasoning", "")[:30],
        "reason_not_healable": "" if status == "healed" else _not_healable_reason(cat, subcat, conf),
        "fixes": fixes,
        "triage_report": report_path,
        "issue_url": "",
        "sha": sha,
        "repo": repo,
    }


def _not_healable_reason(cat: str, subcat: str, conf: float) -> str:
    if conf < CONFIDENCE_MIN_TRIAGE:
        return f"置信度过低（{conf:.2f} < {CONFIDENCE_MIN_TRIAGE}），无法安全自愈"
    if cat == "real_bug":
        return "真实 Bug，需要后端或开发者介入"
    if cat == "flaky_data":
        return "数据问题，需检查 fixture 清理逻辑"
    if cat == "flaky_test" and subcat == "element_missing":
        return "元素不存在，无法确定是延迟渲染还是功能删除，需人工确认"
    if cat == "unknown":
        return "证据不足，无法自动判断"
    return "当前规则不支持自动修复此类错误"


# ─────────────────────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────────────────────

def run(test_results_path: str, output_path: str, repo: str, sha: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client  = anthropic.Anthropic(api_key=api_key) if api_key else None

    # 加载 pytest-json-report 失败列表
    failed = _load_failed_tests(test_results_path)
    if not failed:
        result = {"status": "no_failures", "error_category": "none",
                  "failed_test": "", "confidence": 1.0}
        Path(output_path).write_text(json.dumps(result, indent=2, ensure_ascii=False))
        return result

    all_triage = []
    for test in failed:
        test_name = test["nodeid"].split("::")[-1]
        print(f"\n🔍 Collecting evidence: {test_name}")
        evidence = collect_evidence(test_name)

        if client:
            print(f"🤖 Classifying with Claude...")
            triage = classify_with_claude(client, evidence)
        else:
            print("⚠️  No ANTHROPIC_API_KEY — using mock triage")
            triage = {
                "category": "unknown", "sub_category": None,
                "confidence": 0.0, "matched_rule": "N/A",
                "reasoning": "API key not set",
                "key_evidence": [test.get("longrepr", "")[:200]],
                "suggested_fix_selector": None,
                "fix_pattern": None, "fix_code_before": None, "fix_code_after": None,
            }

        triage["test_name"] = test_name
        evidence["test_name"] = test_name
        all_triage.append({"triage": triage, "evidence": evidence})
        print(f"   → {triage['category']}/{triage.get('sub_category','')} conf={triage['confidence']:.2f}")

    # 生成 Markdown 报告
    report_content = generate_report([t["triage"] for t in all_triage])
    today = datetime.now().strftime("%Y-%m-%d")
    report_path = f"e2e-failure-triage-report-{today}.md"
    idx = 2
    while Path(report_path).exists():
        report_path = f"e2e-failure-triage-report-{today}-{idx}.md"
        idx += 1
    Path(report_path).write_text(report_content, encoding="utf-8")
    print(f"\n📝 Triage report saved: {report_path}")

    # 取置信度最高的失败用例作为 healing-result 的主对象
    primary = max(all_triage, key=lambda x: x["triage"].get("confidence", 0))
    healing = build_healing_result(
        primary["triage"], primary["evidence"], report_path, repo, sha
    )
    healing["total_failed"] = len(failed)

    Path(output_path).write_text(json.dumps(healing, indent=2, ensure_ascii=False))
    print(f"🏥 Healing result: {output_path}  status={healing['status']}")
    return healing


def _load_failed_tests(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        print(f"⚠️  {path} not found, using mock")
        return [{"nodeid": "tests/test_mock.py::test_mock_failure",
                 "outcome": "failed",
                 "longrepr": "TimeoutError: Timeout 5000ms exceeded waiting for locator('[data-testid=\"btn-edit\"]')"}]
    data = json.loads(p.read_text())
    return [t for t in data.get("tests", []) if t.get("outcome") == "failed"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-results", default="test-results.json")
    parser.add_argument("--output",       default="healing-result.json")
    parser.add_argument("--repo",         default="")
    parser.add_argument("--sha",          default="")
    args = parser.parse_args()
    result = run(args.test_results, args.output, args.repo, args.sha)
    sys.exit(0)
