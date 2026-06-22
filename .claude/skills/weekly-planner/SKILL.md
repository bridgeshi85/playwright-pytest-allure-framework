---
name: weekly-planner
description: Generate a personalized weekly plan and sync it to Google Calendar. Use this skill whenever the user says "帮我做周计划", "生成本周计划", "weekly plan", "安排本周任务", "规划这周", "sync tasks to calendar", or any variation of wanting to plan their week. Also trigger when the user says things like "这周我要做什么" or "帮我安排时间". This skill reads tasks from 滴答清单 (TickTick/dida), applies personal scheduling rules, generates time blocks, and creates Google Calendar events — all in one automated flow.
compatibility: Requires dida MCP and Google Calendar MCP connections. Notion MCP optional (for Goals database only).
---

# Weekly Planner Skill

Generate a weekly plan from 滴答清单 tasks → apply scheduling rules → sync to Google Calendar.

## Overview

This skill does 4 things in sequence:
1. **Read** — Fetch P1/P2 tasks from 滴答清单 (dida MCP) + goals from Notion
2. **Assess** — Check Google Calendar for the week's fixed events
3. **Plan** — Apply scheduling rules to build a day-by-day time block plan
4. **Sync** — Create Google Calendar events for each block

Read `references/scheduling-rules.md` before generating the plan — it contains all personal preferences and constraints.

---

## Step 1: Determine and Confirm the Target Week

**⚠️ CRITICAL: Always get explicit date confirmation from the user before proceeding.**

### 1a. Ask for Date Range

If the user says "本周计划" or "weekly plan", immediately ask:

```
📅 请确认本周的日期范围，确保计划准确：

请提供以下信息：

1️⃣ 本周的日期范围
   • 周一（第一天）: YYYY-MM-DD (例: 2026-05-25)
   • 周日（最后一天）: YYYY-MM-DD (例: 2026-05-31)
   
   或者，简单告诉我：
   • 今天是 YYYY-MM-DD (几号)
   我来计算本周的范围
```

### 1b. Validate and Confirm

Once user provides dates, **immediately validate**:

1. **Check the day of week**
   - User says: "2026-05-25 is Monday"
   - Calculate: Is 2026-05-25 actually a Monday? 
   - If NO → Stop and ask: "❌ 2026-05-25 is actually a [WEEKDAY]. 请重新确认日期。"

2. **Verify the range is exactly 7 days**
   - Start date to end date = 7 days?
   - If not → Ask: "⚠️ 这个范围是 X 天，不是 7 天。确定吗？"

3. **Confirm back to user**
   ```
   ✅ 已确认本周范围：
   📅 2026-05-25 (周一) to 2026-05-31 (周日)
   继续生成周计划吗？(Y/N)
   ```

### 1c. Only Proceed After Explicit Confirmation

Do **NOT** proceed to Step 2 until user confirms with "是的" or "Yes" or similar.

If user says "不" or "No" → Ask them to provide corrected dates and repeat 1b.

```
Target week: YYYY-MM-DD (Mon) to YYYY-MM-DD (Sun) [CONFIRMED]
Timezone: [CONFIRMED]
Sports events: [CONFIRMED]
```

---

## Step 2: Read Task Data

### 2a. Fetch Active Goals (Notion — optional)
Read the My Goals database (ID: `8979ec2a-3ae8-4c86-b424-ac1ecac9b905`).

Filter for:
- Year = current year
- Status = "In progress"
- Archive = No

Extract: Goal name, Quarter, Key focus area.

> If Notion MCP is unavailable, skip 2a and proceed directly to 2b.

### 2b. Fetch Priority Tasks from 滴答清单 (Primary Source)

**⚠️ IMPORTANT: 滴答清单 is now the source of truth for tasks. Do NOT read tasks from Notion.**

Use the dida MCP `filter_tasks` tool with `status: [0]` (未完成) to fetch all incomplete tasks.

```
filter_tasks({
  filter: {
    status: [0],
    priority: [5, 3]   // 5 = high (P1), 3 = medium (P2)
  }
})
```

Task priority mapping (dida → plan):
- `priority: 5` = P1 (High) → schedule first
- `priority: 3` = P2 (Medium) → schedule after P1
- `priority: 1` = P3 (Low) → only if time allows
- `priority: 0` = No priority → skip unless user requests

Project mapping:
- `Side Project` → Side project / technical work (color 9)
- `学习` → Learning / study (color 2)
- `博客` → Creation / writing (color 6)
- `工作` → Work tasks (color 8)
- `Inbox` → Triage first; treat as P2 unless tagged P1

For each task, extract:
- `title` → task name
- `priority` → scheduling priority
- `tags` → look for "Doing", "P1", "P2", "AWS", "Rust", etc.
- `dueDate` → deadline constraint
- `projectId` → determines task type and color
- `content` → description / Notion link for reference

Sort order: `tags` contains "Doing" first → `priority: 5` → `priority: 3` → by `dueDate` ascending.

**Rules:**
- Tasks tagged "Doing" = in-progress, highest urgency → schedule in best focus windows first
- Tasks with `dueDate` this week = urgent → schedule before deadline
- Do NOT modify tasks; only read and schedule them
- Tasks in `工作` project = skip (work tasks not scheduled in personal plan unless user requests)

### 2c. If insufficient P1 tasks found
Ask the user: "滴答清单中的 P1 任务不足以填满本周。你想：
1. 从 P2 任务中补充
2. 从 Inbox 补充
3. 使用灵活时间做自主学习/创作

**Never assume or create tasks on behalf of the user.**

---

## Step 3: Read Google Calendar & Build Weekly Constraints Map

### 3a. Fetch Previous Day (Day Before Week Starts)

**⚠️ IMPORTANT: Always fetch Sunday evening before the target week starts.**

Reason: Check for late-night activities (sports events, work blocks) that affect Monday morning energy.

```
Fetch date: target_week_start - 1 day
Check for:
  • Sports events (看球, football, match) evening time
  • Late-night entertainment (游戏, gaming)
  • Late work/project blocks
  
Result:
  IF evening has 看球 (sports watching):
    Monday morning: ⚠️ Low energy expected
    → Recommendation: Skip early-rise Mon, prefer lighter morning tasks
  
  IF no events:
    Monday morning: ✓ Ready for early-rise + deep work
```

### 3b. Fetch Target Week Events

Fetch all events for the target week (Mon–Sun) from the user's primary calendar.

Identify and categorize:
- **Training events** (私教, 训练, 拉伸) → mark those evenings as low-intensity only
- **Sports watching** (看球, football, 球赛, match) → **block morning/afternoon before event**
- **Fixed personal commitments** (family, medical, etc.)
- **Existing work/project blocks** already scheduled

### 3c. Build Weekly Constraint Map

Create a detailed constraint map for each day:

```
Example:

Sun 5/24 (day before):
  20:00–22:00: 看球 (PSG vs Arsenal)
  → Implication: Mon 5/25 morning may have low energy

Mon 5/25:
  morning: ⚠️ Skip early-rise (user had late football)
           Light morning tasks only
  evening: Check for training
           If no training: ✓ Can do 1h focus

Tue 5/26:
  morning: 07:00–08:00 🏗️ Step 2.1 · 决定 Allure 部署方案（备用早起时段）
  evening: ✓ Can do 1h focus only if early-rise in morning

Wed 5/27:
  morning: ✓ Available for early-rise + deep work
  evening: ✓ Can do 1h focus only if early-rise in morning

Thu 5/28:
  19:00–21:00: 私教训练 (training)
  evening: 🔴 Hard block - light ready
  after training: max 1h focus or reading only

Fri 5/29:
  evening: 🔴 FIXED: Entertainment/Gaming/Relaxation (no focus tasks)

Sat 5/30:
  15:00–17:00: 训练 (training block - fixed)
  afternoon: 🔴 Hard block during training
  evening: Check calendar for 看球
           If watching football games: No morning 5/31 focus
           If without watching football games: ✓ Evening free

Sun 5/31:
  morning: IF previous Sat had football games → ⚠️ Light morning
           IF without watching football games → ✓ Normal focus window
  20:30–21:00: 周总结 (weekly review - fixed)
  evening: 🔴 Light activities only

```

### 3d. Constraint Rules Applied

Based on the map, enforce the rules from `references/scheduling-rules.md` **Section 5** (Rules 1–5):

- **Rule 1**: Previous-day late sports watching → skip Mon morning early-rise
- **Rule 2**: Early-rise day → that evening max 1h focus or reading only
- **Rule 3**: Friday evening = hard entertainment block (no focus tasks)
- **Rule 4**: Sports-watching day → next morning no focus/deep work
- **Rule 5**: Training night → light tasks only (reading, light review)

---

## Step 4: Apply Scheduling Rules

Read `references/scheduling-rules.md` for the full rules. Apply the constraint map from Step 3.

### Task Priority Hierarchy (Critical)
**Source of truth: 滴答清单 (dida) tasks only**

1. **Tags contain "Doing"** (In-progress)
   - Highest priority
   - Assign to best focus windows first (weekday mornings, weekend mornings)
   - If multiple "Doing" tasks, sort by dueDate (earliest first)

2. **priority = 5 (P1) + no "Doing" tag**
   - Second tier; assign after "Doing" tasks
   - Check dueDate; if due this week, schedule in good slots

3. **priority = 3 (P2)**
   - Third tier; fill remaining focus windows
   - Can schedule across multiple days if task is large

4. **Inbox project + priority = 5**
   - Fourth tier; fill remaining focus windows

5. **P2+ or Inbox tasks**
   - Only use if P1 fills less than 80% of available focus time
   - Ask user before adding P2 tasks to the plan

### Apply Calendar Constraints to Task Assignment

See `references/scheduling-rules.md` **Section 5** for the full constraint application rules. In summary:

- Check each day's constraint status (🔴 hard block / ⚠️ low energy / ✓ normal)
- If morning is early-rise → that evening max 1h focus or reading only
- Training evenings → reading/light review only, no deep coding or learning
- Morning after late sports → no focus tasks; reading or light activity only
- Friday evenings → hard entertainment block, no focus tasks
- Weekend morning after sports evening → light activities only

### Time Windows & Task Splitting (with Constraints)

See `references/scheduling-rules.md` **Section 5b** (constraint-aware time windows) and **Section 5c** (constraint-aware task splitting) for the full rules.

### Weekly Quota Check

After assigning all tasks, verify the plan meets the weekly targets from `references/scheduling-rules.md` **Section 2**:

| Category | Target |
|----------|--------|
| Learning / Side Project | 5–6h |
| Creation / Writing | 3–4h |
| Reading | 2–3h |
| Entertainment | 4–6h (protected) |

**If a category is unmet:**
- Flag it in the plan (e.g., "⚠️ Writing 1.5h / 3–4h target")
- Suggest where to add time, respecting constraints
- **Do NOT create new tasks** — just identify empty slots where user can choose

---

## Step 5: Generate the Weekly Plan

Output the plan in this format before syncing to calendar:

```
📅 Week of [Mon Date] – [Sun Date]

🎯 本周重点
- Primary: [Top Doing task or highest priority P0]
- Secondary: [Secondary P1 or focus area]

📊 时间预算
- Learning/Side project: Xh 规划 / 5–6h 目标 ✓/⚠️
- Creation/Writing: Xh 规划 / 3–4h 目标 ✓/⚠️
- Reading: Xh 规划 / 2–3h 目标 ✓/⚠️
- Exercise: ✓ (固定)
- Entertainment: ⭕ (已预留)

─────────────────────────────────
📅 每日安排
[按照每天的时间块列出，注明任务名称、时间、和相关标签]

```

Show this to the user and ask: **"这个计划看起来合理吗？有需要调整的吗？确认后我将同步到 Google Calendar。"**

Wait for confirmation before Step 6.

---

## Step 6: Sync to Google Calendar

After user confirms, create one Google Calendar event per time block.

### Event format
- **Title**: `[emoji] [Task name]` (e.g., `🏗️ Step 1.1 · e2e-runner chart`)
- **Description**: Include task details, acceptance criteria if available, Notion task link
- **Color**: 
  - `9` (Blueberry) = Side project / technical work
  - `6` (Tangerine) = Creation / writing
  - `2` (Sage) = Learning / study
  - `7` (Peacock) = Reading
- **Reminder**: 10 minutes before
- **Calendar**: primary

### Batch creation
Create all events in sequence. After all events are created, report:

```
✅ 已同步 X 个事件到 Google Calendar

本周时间分配：
• [Task 1] → Mon 07:00–08:00
• [Task 2] → Mon 20:00–21:30
• ...

📌 记得：
• 周四/五其中一晚预留娱乐时间（已标注）
• 训练后那晚只安排了阅读/轻活动
• 周日 20:30 周总结（如未在日历中，请手动添加）
```

---

## Step 7: Create Notion Weekly Planner Page

After calendar events are synced, create a new page in the Weekly Planner database.

### Database Info
- **Database ID**: `36777260-dd4d-8085-9c0b-000bba1a537b`
- **Parent Page**: https://www.notion.so/89f77260dd4d839b9a70011e80350a30

### Page Properties
Set these when creating the page:
- **Title**: `Week of [Mon Date] – [Sun Date]` (e.g., "Week of May 19 – May 25")
- **Date range** (if database has this field): Mon–Sun of target week
- **Status** (if exists): "Active"

### Page Content

Create the page with this template structure:

```markdown
## 📋 本周计划

[INSERT THE GENERATED WEEKLY PLAN FROM STEP 5]

Full day-by-day breakdown with times and task names.

---

## 📊 本周回顾

### 完成情况

| 类别 | 预计 | 实际 | 完成率 | 备注 |
|------|------|------|--------|------|
| 专注时间 | __h | __h | ___% | |
| 侧项目 | __h | __h | ___% | |
| 学习 | __h | __h | ___% | |
| 运动 | __次 | __次 | ___% | |
| 阅读 | __h | __h | ___% | |

### 什么做得很好？

_在这里填写本周的成就和优势_

### 需要改进的内容

_在这里记录遇到的瓶颈和下周的调整方向_
```

### How to Fill This

- **完成情况表**: 预计值根据 Step 4 生成的计划计算。实际值在周末回顾时填入。
- **什么做得很好？**: 周末（通常周五晚或周日晚）回顾时填写
- **需要改进的内容**: 列出本周遇到的障碍，为下周调整提供反馈

### Report to User

After the page is created, report:

```
✅ 已创建 Notion 周计划页面

页面链接: [Page URL]

模板已准备就绪：
• 📋 本周计划（已填充）
• 📊 本周回顾（待周末填写）

💡 记得：
• 每晚在日历事件中简短记录完成情况
• 周末（周五晚或周日晚）花 10min 填完回顾表
• 下周日 20:30 基于此页面的反馈生成新的周计划
```

---

## Error Handling

### Date & Time Validation Errors
- **Date format invalid**: Ask user to provide in YYYY-MM-DD format
- **Day of week mismatch**: "❌ 2026-05-25 is actually [WEEKDAY], not Monday. Please reconfirm dates."
- **Range not 7 days**: "⚠️ This range is X days, not a full week. Continue anyway? (Y/N)"
- **Timezone ambiguous**: Confirm user's timezone before proceeding
- **Sports event time unverified**: Ask user to double-check time and timezone

### Notion & Calendar Errors
- **Notion task fetch fails**: Ask user to manually input task list, then proceed from Step 4
- **Calendar conflict detected**: Flag the conflict, suggest alternative slot, ask user to decide
- **Too many tasks for the week**: Show overflow tasks, ask user which to defer to next week
- **Missing estimated time on tasks**: Default to 1.5h per task, note the assumption
