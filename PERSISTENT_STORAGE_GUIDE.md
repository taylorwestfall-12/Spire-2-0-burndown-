# Persistent Daily Actuals - How It Works

## 🎯 Problem This Solves

**Old Approach (BROKEN):**
- Retroactively calculate historical bug counts from ClickUp
- Data changes when bugs are moved between milestones after the fact
- Different counting methods create discontinuities (May 21 → May 22 drop)
- Historical data keeps changing every time we recalculate

**New Approach (FIXED):**
- **`daily_actuals.json`** is the append-only source of truth
- Each day: Fetch from ClickUp → Count → Append to file
- **Never recalculate past dates** - trust what was recorded that day
- Historical data is stable and git-tracked

---

## 📁 Key Files

### `daily_actuals.json` (Git-tracked, ~2 KB)
**Source of truth for all daily bug counts.**

```json
{
  "metadata": {
    "description": "Daily active bug counts - append-only historical record",
    "filter_logic": "2.0.0 Global, excludes Closed/Won't Fix, excludes QA Status Won't Fix/Not a Bug/Duplicated/QA Pass"
  },
  "daily_counts": [
    {
      "date": "2026-05-11",
      "count": 201,
      "source": "historical_baseline"
    },
    {
      "date": "2026-06-02",
      "count": 46,
      "source": "clickup_live_count",
      "timestamp": "2026-06-02T15:00:00"
    }
  ]
}
```

**Rules:**
- ✅ Append new dates
- ✅ Update today's count (if running multiple times per day)
- ❌ NEVER modify historical dates (past entries are immutable)
- ✅ Commit to git after each update

---

## 🔄 New Workflow

### Daily Automation (GitHub Actions - 3x daily)

```bash
# Step 1: Fetch & Count from ClickUp (appends to daily_actuals.json)
python update_daily_actuals.py
  ↓
  Runs: clickup_batch_fetcher.py → spire_bugs_complete.json (121 MB, not in git)
  Runs: parse_and_map_milestones.py → bugs_with_parsed_dates.json (843 KB, not in git)
  Counts active bugs using qa_status_utils filter
  Appends/updates today's count in daily_actuals.json ✅ GIT-TRACKED

# Step 2: Regenerate Dashboard (reads from daily_actuals.json)
python generate_dashboard_from_daily_actuals.py
  ↓
  Loads daily_actuals.json (source of truth)
  Calculates ideal line (from start to Code Freeze)
  Calculates estimated line (last 10 business days rate)
  Saves: burndown_projections.json
  Generates: docs/index.html
  Generates: burndown_chart.png + slack_message.json

# Step 3: Commit & Push
git add daily_actuals.json docs/index.html burndown_projections.json burndown_chart.png slack_message.json
git commit -m "Auto-update: 46 bugs, 3 days to freeze"
git push
```

---

## 🛠️ Manual Operations

### Update Today's Count Manually

```bash
# Full workflow (fetch + count + regenerate)
python update_daily_actuals.py
python generate_dashboard_from_daily_actuals.py

# Commit
git add daily_actuals.json docs/index.html burndown_projections.json
git commit -m "Manual update: [description]"
git push
```

### Backfill a Missing Date

If you discover a date is missing (e.g., automation failed):

```bash
# 1. Manually add the entry to daily_actuals.json
{
  "date": "2026-06-03",
  "count": 38,
  "source": "manual_backfill",
  "note": "Automation failed, manually counted from ClickUp"
}

# 2. Regenerate dashboard
python generate_dashboard_from_daily_actuals.py

# 3. Commit
git add daily_actuals.json docs/index.html burndown_projections.json
git commit -m "Backfill: June 3 count (automation failure)"
git push
```

### Fix an Incorrect Count

If you discover today's count was wrong:

```bash
# 1. Edit daily_actuals.json - change the count for today's date
# 2. Regenerate
python generate_dashboard_from_daily_actuals.py

# 3. Commit
git add daily_actuals.json docs/index.html burndown_projections.json
git commit -m "Fix: Corrected June 2 count (was 50, should be 46)"
git push
```

**Important:** Only fix TODAY or very recent dates. Never change historical data unless there's a critical error.

---

## 🚫 What NOT to Do

### ❌ Don't Retroactively Recalculate Historical Data

```bash
# BAD - Don't do this!
python recalculate_actuals_with_qa_filter.py  # Recalculates May 11 - June 2
```

**Why?** Because:
- Bugs move between milestones after the fact
- ClickUp data changes (status changes, QA Status updates)
- Your counting logic might have evolved
- Historical data becomes unstable

**Instead:** Trust what was recorded on each day. If there's a known error in a past date, manually edit `daily_actuals.json` and document why.

### ❌ Don't Delete `daily_actuals.json`

This file is your source of truth! If deleted, you lose all historical data.

**If accidentally deleted:**
1. Restore from git: `git checkout daily_actuals.json`
2. If not in git yet, reconstruct from `complete_actuals_may11_jun02.json` (one-time migration)

### ❌ Don't Manually Edit Old Dates Without Documentation

If you must edit a historical date:
1. Add a `"note"` field explaining why
2. Add a `"corrected_date"` timestamp
3. Document in git commit message

```json
{
  "date": "2026-05-15",
  "count": 189,
  "source": "historical_actuals_5_11_to_5_21.json",
  "note": "Corrected from 195 - original count included WON'T FIX bugs",
  "corrected_date": "2026-06-02T16:00:00"
}
```

---

## 📊 How Projections Are Calculated

### Actual Line (Green)
- **Source:** `daily_actuals.json` → `daily_counts` array
- **No calculation** - just plots the recorded counts
- Weekend plateaus are visible in the recorded data

### Ideal Line (Black)
- **Start:** First date in `daily_actuals.json` (May 11, 201 bugs)
- **Target:** Zero bugs by Code Freeze (June 4)
- **Rate:** `-201 / business_days_to_freeze`
- **Plateaus:** Weekends

### Estimated Line (Orange)
- **Start:** Last date in `daily_actuals.json` (today's actual count)
- **Rate:** Last 10 business days from `daily_actuals.json`
  - If < 10 business days: Use historical rate (-3.8 bugs/day)
- **Target:** Go Live date (June 15)
- **Plateaus:** Weekends

---

## 🔍 Verifying Data Integrity

### Check for Gaps

```bash
python -c "
import json
from datetime import datetime, timedelta

with open('daily_actuals.json') as f:
    data = json.load(f)

dates = [datetime.strptime(e['date'], '%Y-%m-%d') for e in data['daily_counts']]
dates.sort()

gaps = []
for i in range(len(dates)-1):
    diff = (dates[i+1] - dates[i]).days
    if diff > 1:
        gaps.append(f'{dates[i].strftime(\"%Y-%m-%d\")} → {dates[i+1].strftime(\"%Y-%m-%d\")} (gap: {diff} days)')

if gaps:
    print('⚠️ Found gaps:')
    for gap in gaps:
        print(f'  {gap}')
else:
    print('✅ No gaps in daily actuals')
"
```

### Check for Duplicates

```bash
python -c "
import json

with open('daily_actuals.json') as f:
    data = json.load(f)

dates = [e['date'] for e in data['daily_counts']]
duplicates = [d for d in dates if dates.count(d) > 1]

if duplicates:
    print('❌ Found duplicates:', set(duplicates))
else:
    print('✅ No duplicate dates')
"
```

### View Recent History

```bash
python -c "
import json

with open('daily_actuals.json') as f:
    data = json.load(f)

print('Last 10 days:')
for entry in data['daily_counts'][-10:]:
    print(f'  {entry[\"date\"]}: {entry[\"count\"]:3d} bugs ({entry.get(\"source\", \"unknown\")})')
"
```

---

## 🎓 Migration from Old System

**One-time migration (already done on June 2, 2026):**

```bash
# Created daily_actuals.json from:
# - historical_actuals_5_11_to_5_21.json (May 11-21)
# - Retroactive calculation (May 22 - June 1)
# - Live ClickUp count (June 2)

# All future updates use update_daily_actuals.py
```

---

## ✅ Success Criteria

**You know the system is working when:**

1. ✅ `daily_actuals.json` grows by 1 entry per day
2. ✅ GitHub Actions runs 3x daily without errors
3. ✅ Dashboard shows smooth trend line (no discontinuities)
4. ✅ Historical data doesn't change when you regenerate
5. ✅ File size of `daily_actuals.json` stays small (~2-5 KB)

**Red flags:**

- ❌ Gaps in `daily_actuals.json` (missing dates)
- ❌ Historical counts changing between regenerations
- ❌ GitHub Actions failing with "file not found"
- ❌ Large jumps in counts on business days (check for bugs moved between milestones)

---

**Last updated:** June 2, 2026  
**Status:** ✅ Production ready
