"""
ai/healer/agent.py
Healer Agent — 错误分类 → 根因分析 → 自愈或创建 Issue
"""

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic

# ── 内置错误分类体系（也可从 error_taxonomy.json 加载）──────────────
ERROR_TAXONOMY = {
    "locator_broken": {
        "name": "Locator 失效",
        "patterns": ["element not found", "no matching element",
                     "selector did not match", "locator.click", "strict mode violation"],
        "severity": "high",
        "healable": True,
        "healing_rules": ["try_alternative_locator", "add_explicit_wait"],
    },
    "timeout": {
        "name": "超时问题",
        "patterns": ["timeout", "waiting for", "deadline exceeded",
                     "Timeout", "TimeoutError"],
        "severity": "medium",
        "healable": True,
        "healing_rules": ["increase_timeout", "add_wait_for_visibility"],
    },
    "assertion_failed": {
        "name": "断言失败",
        "patterns": ["AssertionError", "assert ", "expected", "but found",
                     "Expected", "to equal", "to contain"],
        "severity": "medium",
        "healable": False,
        "reason": "断言失败通常表示业务逻辑问题，不能自动修复",
        "action": "create_issue",
    },
    "environment_issue": {
        "name": "环境问题",
        "patterns": ["connection refused", "network error",
                     "502", "503", "ECONNREFUSED", "ERR_CONNECTION"],
        "severity": "low",
        "healable": False,
        "reason": "环境问题需要 DevOps 介入",
        "action": "create_issue_with_label:infrastructure",
    },
    "flaky_test": {
        "name": "不稳定测试",
        "patterns": ["flaky", "intermittent", "random failure",
                     "sometimes fails", "occasionally"],
        "severity": "medium",
        "healable": True,
        "healing_rules": ["add_retry_logic", "increase_wait_time"],
    },
}


def classify_error(error_message: str) -> tuple[str, dict]:
    """Pattern matching 优先，匹配不到时返回 unknown"""
    for category_id, category in ERROR_TAXONOMY.items():
        if any(p.lower() in error_message.lower() for p in category["patterns"]):
            return category_id, category
    return "unknown", {"name": "未知错误", "healable": False,
                       "reason": "无法匹配已知错误类型", "action": "create_issue"}


def analyze_with_claude(client: anthropic.Anthropic,
                        error_message: str,
                        category_name: str,
                        test_name: str) -> dict:
    """用 Claude 做根因分析，返回结构化结果"""
    prompt = f"""你是一个 Playwright 测试故障分析专家。

测试名称：{test_name}
错误分类：{category_name}
错误信息：
```
{error_message[:2000]}
```

请分析这个错误，以 JSON 格式返回，不要加任何 markdown 包裹：
{{
  "root_cause": "根本原因（一句话）",
  "immediate_cause": "直接原因",
  "recommendation": "修复建议（具体可操作）",
  "confidence": 0.0,
  "fix_summary": "修复摘要（10字以内）"
}}

confidence 是你对根因分析的置信度，0-1 之间。"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # 容错：提取 JSON 部分
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        return {
            "root_cause": raw[:200],
            "immediate_cause": "",
            "recommendation": "",
            "confidence": 0.3,
            "fix_summary": "分析结果解析失败",
        }


def load_test_results(results_path: str) -> list[dict]:
    """加载 pytest-json-report 的结果"""
    path = Path(results_path)
    if not path.exists():
        print(f"⚠️  test-results.json not found at {results_path}, using mock failure")
        return [{
            "nodeid": "tests/test_login.py::test_login_success",
            "outcome": "failed",
            "longrepr": "AssertionError: expected 'Welcome' but found 'Login'\nassert home_page.get_title() == 'Welcome'",
        }]

    with open(path) as f:
        data = json.load(f)

    failed = []
    for test in data.get("tests", []):
        if test.get("outcome") == "failed":
            failed.append({
                "nodeid": test.get("nodeid", "unknown"),
                "outcome": "failed",
                "longrepr": test.get("call", {}).get("longrepr", ""),
            })
    return failed


def run_healer(test_results_path: str, output_path: str,
               repo: str, sha: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key) if api_key else None

    failed_tests = load_test_results(test_results_path)

    if not failed_tests:
        result = {
            "status": "no_failures",
            "message": "No failed tests found",
            "error_category": "none",
        }
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        return result

    # 取第一个失败的 test 分析（可扩展为多个）
    test = failed_tests[0]
    error_message = test.get("longrepr", "")
    test_name = test.get("nodeid", "unknown")

    print(f"🔍 Analyzing: {test_name}")

    # Step 1: 错误分类
    category_id, category = classify_error(error_message)
    print(f"📂 Category: {category_id} ({category['name']})")

    # Step 2: Claude 根因分析
    analysis = {}
    if client:
        print("🤖 Running Claude root cause analysis...")
        analysis = analyze_with_claude(client, error_message, category["name"], test_name)
    else:
        print("⚠️  ANTHROPIC_API_KEY not set, skipping Claude analysis")
        analysis = {
            "root_cause": "API key not configured",
            "immediate_cause": error_message[:200],
            "recommendation": "Please configure ANTHROPIC_API_KEY secret",
            "confidence": 0.0,
            "fix_summary": "No analysis",
        }

    confidence = analysis.get("confidence", 0.0)
    healable = category.get("healable", False)

    # Step 3: 决策
    if healable and confidence >= 0.75:
        status = "healed"
        print(f"✅ Healable with confidence {confidence:.0%} — generating fix...")
        # 这里预留 fix 代码生成（Phase 2 Step 2/3 实现）
        fixes = []
    else:
        status = "not_healable"
        if healable:
            print(f"⚠️  Healable but confidence too low ({confidence:.0%} < 75%)")
        else:
            print(f"❌ Not healable: {category.get('reason','')}")

    result = {
        "status": status,
        "failed_test": test_name,
        "error_category": category_id,
        "error_category_name": category["name"],
        "error_message": error_message[:500],
        "root_cause": analysis.get("root_cause", ""),
        "immediate_cause": analysis.get("immediate_cause", ""),
        "recommendation": analysis.get("recommendation", ""),
        "confidence": confidence,
        "fix_summary": analysis.get("fix_summary", ""),
        "reason_not_healable": category.get("reason", ""),
        "fixes": fixes if status == "healed" else [],
        "issue_url": "",   # create-issue job 回填
        "sha": sha,
        "repo": repo,
        "total_failed": len(failed_tests),
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"📝 Healing result written to {output_path}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Healer Agent")
    parser.add_argument("--test-results", default="test-results.json")
    parser.add_argument("--output", default="healing-result.json")
    parser.add_argument("--repo", default="")
    parser.add_argument("--sha", default="")
    args = parser.parse_args()

    result = run_healer(args.test_results, args.output, args.repo, args.sha)
    print(f"\n🏥 Final status: {result['status']}")
    sys.exit(0)
