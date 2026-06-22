# Personal Scheduling Rules Reference

> Last updated: 2026-05-21
> This file is the source of truth for all scheduling decisions.

---

## 1. Training & Exercise Schedule

### Weekly Fixed Training
- **2× stretching sessions** + **2× strength training sessions** per week
- **Saturday 15:00**: Combined block — strength training + stretching + run (all-in-one, ~2–3h)
  - Do NOT schedule any tasks Saturday afternoon
  - This is a hard block, never move it

### Additional Cardio
- 1–2× additional aerobic runs per week
- Prefer weekend mornings (before 9am) or weekday evenings when not training
- Sunday run is common — check calendar for confirmed time

### Training Night Rule
- Evenings with private training (私教) = **light tasks only**
- Allowed after training: reading, casual entertainment, light review
- NOT allowed after training: deep coding, new technical learning, writing

---

## 2. Weekly Personal Targets (Quotas)

These are minimums to hit each week:

| Category | Weekly Target | Notes |
|----------|--------------|-------|
| Learning / Side Project | 5–6h | Technical study, project work combined |
| Creation | 3–4h | Blog writing, technical articles, project output |
| Reading | 2–3h | Books, light input — not technical docs |
| Entertainment | 4–6h | Gaming, relaxing — protect this, don't squeeze it out |

**Football watching**: Saturday and/or Sunday evenings — times are in Google Calendar. Always check calendar. Never schedule tasks after football starts.

---

## 3. Focus Windows & Energy Map

### Best Hours for Deep Work
- **07:00–08:00** (weekday mornings): Highest quality focus — reserve for hardest tasks
  - Only available on early-rise days (1–2 days/week, user's choice each week)
  - Do NOT schedule past 08:00 on workday mornings (leave home at 08:45)

### Weekday Evening Focus Nights
Unlock full evening focus on **Mon, Tue, Thu only**:
- Window: **20:00–21:30** (1.5h max)
- These are the core weekday productivity slots

### Weekend Windows
- **Sat/Sun morning 10:00–12:00**: 2h deep work block (best weekend slot)
- **Weekend afternoon**: flexible; Saturday afternoon = training (blocked)
- **Weekend evening**: check calendar for football; if no football, available for light tasks

### Weekly contribution logic
```
Weekday mornings (1–2 early rise days):  1h × 2 = 2h
Weekday evenings (Mon/Tue/Thu):          1.5h × 3 = 4.5h
Weekend mornings (Sat/Sun):              2h × 2 = 4h
─────────────────────────────────────────────────────
Total available: ~10.5h focused work/week
Target: 10–14h across all categories
```

---

## 4. Scheduling Principles

### Morning Blocks
- 07:00–08:00 = deep learning or coding (highest cognitive demand)
- Never schedule entertainment or low-value tasks in the morning window
- If task requires >1h: split — do first half morning, second half evening

### After-Training Evenings (Tue/Thu/Fri)
- **Allowed**: reading (30–60min), light entertainment, weekly review
- **Not allowed**: new technical learning, side project coding, writing
- If Fri is the gaming/rest night: no tasks at all after 20:00

### Football Night Rule
- Check Google Calendar for football events before scheduling
- Once football is on calendar: no tasks scheduled after kick-off time
- Next morning (post football): avoid high-intensity scheduling — prefer reading or light activity

### Sat/Sun Balance
- Don't schedule high-intensity learning AND high-intensity creation on the same weekend day
- Alternate: one day = learning/project, other day = creation/reading
- Keep Sunday evening light: weekly review (20:30, 30min max) + relaxation

### Task Splitting Rules
| Task Duration | Weekday Rule | Weekend Rule |
|---------------|-------------|--------------|
| ≤ 1h | Single session | Single session |
| 1–1.5h | Single session (evening) or split | Single session (morning) |
| 1.5–2h | Split: 1h + 0.5h across two sessions | Single session (morning) |
| > 2h | Must split across multiple days | Split: 2h + remainder next day |

### Buffer Rule
- Never fill more than 80% of available focus time
- Always leave at least one evening/session unscheduled as overflow buffer
- Tasks with complexity tag (#困难) get 1.5× time buffer

---

## 5. Calendar Constraint Rules (Critical for Accuracy)

### Rule 1: Check Previous Day for Late Sports
**Reason**: Late-night sports watching (看球) affects next morning energy

```
Before generating the plan:
  Fetch calendar events on [target_week_start - 1 day]
  
  IF evening has 看球/sports watching:
    THEN:
      Mon morning: ❌ Do NOT schedule early-rise
      Mon morning: Skip focus tasks or light activity only
      Note: "⚠️ Late football Sun night → Mon morning low energy"
  
  IF no late events:
    Mon morning: ✓ Normal early-rise window available
```

### Rule 2: Early-Rise Day Evening Restriction
**Reason**: Waking at 6am + 8h work → evening fatigue accumulation

```
IF user chooses early-rise on day D (e.g., Mon or Wed):
  THEN evening of day D:
    ✅ Allowed: reading (1h), light review, entertainment
    ❌ NOT allowed: deep coding (>1h), learning, heavy writing
    Limit: max 1h focus task OR reading only
```

### Rule 3: Friday Evening = Fixed Entertainment Block
**Reason**: Mental recovery before weekend + consistent schedule

```
Every Friday evening (after 18:00 or 20:00):
  🔴 HARD BLOCK: Reserved for entertainment/gaming/relaxation
  No focus tasks allowed
  
  Special case: If Friday is an early-rise day:
    Friday evening: EVEN lighter (max reading, no tasks at all)
```

### Rule 4: Sports Watching Blocks Next Morning Focus
**Reason**: Late-night sleep → low morning cognitive capacity

```
IF day D has evening 看球 (any time):
  THEN day D+1 morning:
    ❌ DO NOT schedule focus/deep work tasks
    ✓ OK: reading, light activity, planning
  
  Weekend special:
    IF Sat evening has 看球: Sun morning is light
    IF Sun evening has 看球: Mon morning should skip early-rise
```

### Rule 5: Training Night = Light Tasks Only
**Reason**: Physical fatigue after private training reduces cognitive capacity

```
IF evening has 私教/训练 (training session):
  THEN that evening:
    ✅ Allowed: reading, casual entertainment, light review
    ❌ NOT allowed: deep coding, new technical learning, writing
```

### Applying Constraints to Task Assignment

For each task being assigned, check the day's constraint status:

1. **Hard block** (🔴): training, sports watching, Friday entertainment
   - Do not assign focus tasks; reading/light activity only

2. **Low energy** (⚠️): morning after late sports watching
   - Skip focus tasks; prefer reading or light activity

3. **Early-rise impact**: if morning is early-rise (07:00–08:00)
   - That evening: max 1h focus OR reading only

---

## 5b. Constraint-Aware Time Windows

These are the base time windows (Section 3) with constraint overrides applied:

- **Morning focus (07:00–08:00)** on early-rise days:
  - ❌ NOT on mornings after 看球 (Rule 4)
  - ❌ NOT if that evening is Friday (Rule 3)

- **Weekday evening focus (20:00–21:00)** on Mon, Tue, Thu:
  - ❌ NOT on training nights (Rule 5)
  - ❌ NOT on Friday evening (Rule 3)
  - ⚠️ If morning was early-rise: max 1h or reading only (Rule 2)

- **Weekend morning (09:00–11:00)**:
  - ❌ NOT if previous evening had 看球 (Rule 4)
  - ✓ OK if no constraints apply

- **Weekend afternoon**: flexible; Saturday afternoon = training hard block (never move)

---

## 5c. Constraint-Aware Task Splitting

| Situation | Split Rule |
|-----------|-----------|
| Task > 1h on a weekday, morning is early-rise | morning 1h + evening light only (reading / 0.5h max) |
| Task > 1h on a weekday, evening has training | morning or next-day session; do NOT use training evening |
| Task > 2h on weekend | Split with break, or across Sat + Sun; avoid Sat afternoon training block |
| Task on Sat, Sat evening has 看球 | Finish before football kick-off; do not spill into evening |

- Frequency: 1–2 days per week (Mon–Fri only)
- Wake time: 06:00
- Focus window: 07:00–08:00 (1h, not 1.5h — need time to wake up, prepare)
- Choice of which days: flexible, user decides each week based on energy
- Do NOT assume every weekday has a morning session

**Scheduling logic**: When allocating morning slots, use max 2 mornings per week. Prefer Mon and Wed, or Mon and Thu — avoid back-to-back early rises more than twice unless user specifies.

---

## 6. Weekly Rhythm Pattern (Reference)

```
TYPICAL WEEK PATTERN:

Mon  AM: [early rise possible] 07–08 deep work
     PM: 20:00–21:00 focus (project or learning)

Tue  AM: [no early rise usually]
     PM: training → light only (reading)

Wed  AM: [early rise possible] 07–08 deep work  
     PM: 20:00–21:00 focus (creation preferred)

Thu  AM: [no early rise]
     PM: training → THEN 20:00–21:00 focus OR gaming night (pick one)

Fri  AM: [no early rise]
     PM: training → rest/gaming (gaming night if not Thu)

Sat  AM: 09:00–11:00 deep work (2h)
     PM: 15:00–17:00 TRAINING BLOCK (fixed, never move)
     PM: football if on calendar

Sun  AM: 09:00–10:30 reading or light creation (1.5h)
     PM: flexible
     PM: 20:30 weekly review (30min, fixed)
```

---

## 7. Task Type → Best Time Slot Mapping

| Task Type | Best Slot | Backup Slot |
|-----------|-----------|-------------|
| Deep coding / debugging | Weekday morning, Weekend morning | Weekday evening (Mon/Tue/Thu) |
| New technical learning | Weekday morning | Weekend morning |
| Writing / blog | Weekday evening (Wed preferred) | Weekend morning |
| Reading | Training evenings, before sleep | Weekend afternoon |
| Planning / review | Sunday evening 20:30 | Friday evening |
| Light admin / notes | Any light slot | — |
| Entertainment / gaming | Thu or Fri evening | Weekend evening |

---

## 8. Data Sources

### 任务数据（滴答清单 — Primary）

| 项目 | Project ID | 颜色 |
|------|-----------|------|
| Side Project | `6a3937a5e4b0c21701372703` | 9 Blueberry |
| 学习 | `6a0eb2f7e4b0e19c5406dc93` | 2 Sage |
| 博客 | `63fa42d3e4b08c89b2fe8598` | 6 Tangerine |
| 工作 | `6a0eb309e4b0e19c5406dde1` | 8 Graphite（通常跳过）|
| Inbox | `inbox` | 按 tag 决定颜色 |

Priority 映射：`5` = P1 高优先级 / `3` = P2 中优先级 / `1` = P3 低优先级 / `0` = 无优先级

### Notion（Optional — Goals Only）

| Resource | ID |
|----------|-----|
| My Goals database | `8979ec2a-3ae8-4c86-b424-ac1ecac9b905` |
| Personal Home Projects | `e8f390d1-70cd-4467-be92-aefe0cbf1bf9` |
| Second Brain hub | `36377260-dd4d-811b-8afd-d899e5f23de7` |
| **Weekly Planner database** | `36777260-dd4d-8085-9c0b-000bba1a537b` |

---

## 9. Google Calendar Event Colors

| Color ID | Color Name | Use For |
|----------|-----------|---------|
| 9 | Blueberry | Side project / technical work |
| 6 | Tangerine | Creation / writing / blog |
| 2 | Sage | Learning / study / courses |
| 7 | Peacock | Reading |
| 5 | Banana | Planning / review |
| 3 | Grape | Entertainment / gaming |
| 4 | Flamingo | Training / exercise |
