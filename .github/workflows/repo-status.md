---
description: |
  This workflow creates daily repo status reports. It gathers recent repository
  activity (issues, PRs, discussions, releases, code changes) and generates
  engaging GitHub issues with productivity insights, community highlights,
  and project recommendations.

on:
  schedule: daily
  workflow_dispatch:

engine:
  id: codex
  model: auto
  env:
    OPENAI_BASE_URL: https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}


permissions:
  contents: read
  issues: read
  pull-requests: read

  copilot-requests: none

network:
  allowed:
    - defaults
    - token-plan.cn-beijing.maas.aliyuncs.com

tools:
  bash: ["*"]
  edit: false
  github:
    lockdown: false
    min-integrity: none

safe-outputs:
  mentions: false
  allowed-github-references: []
  create-issue:
    title-prefix: "[repo-status] "
    labels: [report, daily-status]
    close-older-issues: true

---

# Repo Status

Create an upbeat daily status report for the repo as a GitHub issue.

## What to include

- Recent repository activity (issues, PRs, discussions, releases, code changes)
- Progress tracking, goal reminders and highlights
- Project status and recommendations
- Actionable next steps for maintainers

## Style

- Be positive, encouraging, and helpful 🌟
- Use emojis moderately for engagement
- Keep it concise - adjust length based on actual activity

## Process

1. Gather recent activity from the repository
2. Study the repository, its issues and its pull requests
3. Create a new GitHub issue with your findings and insights
