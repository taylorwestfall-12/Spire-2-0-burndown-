# ClickUp vs. Dashboard Bug Count Discrepancy Analysis

**Date**: June 2, 2026  
**ClickUp Shows**: 32 active bugs  
**Dashboard Shows**: 47 active bugs  
**Difference**: 15 bugs

## Root Cause: QA Status Field Filter

The ClickUp dashboard view applies a filter on the **"QA Status (sp)"** custom field that our burndown script does not apply.

### ClickUp Filter Logic

ClickUp's "2.0.0 Global" view appears to filter to only show bugs where:
- **Spire Release** = "2.0.0 Global" ✅
- **Status** ≠ Closed/Won't Fix ✅
- **QA Status (sp)** = "QA Review" (1) OR "Open" (4) ⚠️ **<-- This filter is missing from our script**

### Our Current Filter Logic

Our burndown script (`update_today_burndown.py`) currently only filters by:
- **Spire Release** = "2.0.0 Global" ✅
- **Status** ≠ Closed/Won't Fix ✅

**Missing**: We do NOT filter by QA Status field.

## Bug Count Breakdown

| Category | Count | Included in ClickUp? | Included in Dashboard? |
|----------|-------|---------------------|----------------------|
| **QA Status = "QA Review"** | 15 | ✅ Yes | ✅ Yes |
| **QA Status = "Open"** | 18 | ✅ Yes | ✅ Yes |
| **QA Status = "Triage"** | 3 | ❌ No | ✅ Yes |
| **QA Status = "Ready for Test"** | 2 | ❌ No | ✅ Yes |
| **QA Status = None** | 7 | ❌ No | ✅ Yes |
| **QA Status = "Fix in Progress"** | 1 | ❌ No | ✅ Yes |
| **QA Status = "Won't Fix"** | 1 | ❌ No | ✅ Yes (but should be excluded!) |
| **Total Active** | **47** | **33** | **47** |

## Recommendation

We have **three options**:

### Option 1: Match ClickUp's Filter (Recommended)
**Update our script to only count bugs with QA Status = "QA Review" or "Open"**

**Pros**:
- Dashboard matches ClickUp's internal view exactly (32-33 bugs)
- Only tracks bugs actively in the QA/Dev workflow
- Excludes bugs in "Triage", "Ready for Test", or without QA Status

**Cons**:
- More complex filtering logic
- Need to maintain QA Status field mapping

**Implementation**: Update `update_today_burndown.py` to filter:
```python
excluded_qa_statuses = [10, 11, 12, 13]  # Duplicated, Not a Bug, Won't Fix, QA Pass
included_qa_statuses = [1, 4]  # QA Review, Open

active_bugs = [
    bug for bug in bugs
    if bug.get('milestone_simplified') == '2.0.0 Global'
    and bug.get('status') not in excluded_statuses
    and get_qa_status(bug) in included_qa_statuses
]
```

### Option 2: Exclude QA Status "Won't Fix" Only
**Add QA Status "Won't Fix" (12) to excluded statuses**

**Pros**:
- Simple change (just exclude 1 additional status)
- Fixes the obvious bug (counting "Won't Fix" as active)

**Cons**:
- Still won't match ClickUp (46 vs 32)
- Still counts bugs in "Triage", "Ready for Test", etc.

**Implementation**:
```python
excluded_qa_statuses = [10, 11, 12, 13]  # Duplicated, Not a Bug, Won't Fix, QA Pass

active_bugs = [
    bug for bug in bugs
    if bug.get('milestone_simplified') == '2.0.0 Global'
    and bug.get('status') not in excluded_statuses
    and get_qa_status(bug) not in excluded_qa_statuses
]
```
This would give us **46 active bugs** vs. ClickUp's 32.

### Option 3: Keep Current Logic, Document Difference
**No code changes, just document why counts differ**

**Pros**:
- No code changes needed
- Shows the "true" count of all non-closed bugs

**Cons**:
- Dashboard doesn't match ClickUp (confusing to stakeholders)
- Includes bugs that aren't actually in active development

## QA Status Field Reference

| Value | Name | Meaning | Should Count? |
|-------|------|---------|---------------|
| 0 | Ready for Test | Awaiting QA | ❌ Not in ClickUp view |
| 1 | QA Review | In QA review | ✅ Yes |
| 2 | Need Info/Testing/Confirmation | Blocked | ❌ Not in ClickUp view |
| 3 | Triage | Needs triage | ❌ Not in ClickUp view |
| 4 | Open | Active/Open | ✅ Yes |
| 5 | Reopened | Reopened after fix | ❌ Not in ClickUp view |
| 6 | Blocked | Blocked | ❌ Not in ClickUp view |
| 7 | Fix in Progress | Dev working on it | ❌ Not in ClickUp view |
| 8 | Pending Build | Awaiting build | ❌ Not in ClickUp view |
| 9 | Not Reproducible | Can't repro | ❌ Should exclude |
| 10 | Duplicated | Duplicate | ❌ Should exclude |
| 11 | Not a Bug | Not a bug | ❌ Should exclude |
| 12 | Won't Fix | Won't fix | ❌ Should exclude |
| 13 | QA Pass | QA passed | ❌ Should exclude |
| 14 | Logs | Logs only | ❌ Not in ClickUp view |
| None | (not set) | No QA status | ❌ Not in ClickUp view |

## Current Status

**Our Script**:
- Filters by Status field only
- Counts: 47 active bugs

**ClickUp Dashboard**:
- Filters by Status + QA Status
- Shows: 32 active bugs

**Difference**: 15 bugs (those with QA Status ≠ "QA Review" or "Open")

## Next Steps

**Recommended**: Implement Option 1 to match ClickUp's filter exactly.

This will ensure the burndown dashboard always matches the team's internal ClickUp view.
