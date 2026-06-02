#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update Daily Actuals - Persistent Historical Record

This script:
1. Fetches current bug data from ClickUp
2. Parses the data to get simplified format
3. Counts today's active bugs
4. Appends/updates today's count in daily_actuals.json
5. NEVER modifies historical data - append-only!

This is the NEW approach - daily_actuals.json is the source of truth.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
DAILY_ACTUALS_FILE = "daily_actuals.json"
BUGS_FILE = "bugs_with_parsed_dates.json"
TODAY = datetime.now().date()


def fetch_and_parse_clickup_data():
    """
    Fetch latest bug data from ClickUp and parse it.

    Returns:
        bool: True if successful, False otherwise
    """
    print("📡 Fetching latest bug data from ClickUp...")

    try:
        # Step 1: Fetch from ClickUp
        result = subprocess.run(
            [sys.executable, 'clickup_batch_fetcher.py'],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Fetched from ClickUp")

        # Step 2: Parse and map milestones
        result = subprocess.run(
            [sys.executable, 'parse_and_map_milestones.py'],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Parsed bug data")

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Error fetching/parsing data: {e}")
        return False


def count_active_bugs():
    """
    Count current active 2.0.0 bugs.

    Uses the same filter logic as update_today_burndown.py:
    - Milestone = "2.0.0 Global"
    - Main Status ≠ Closed/Won't Fix
    - QA Status ≠ Won't Fix/Not a Bug/Duplicated/QA Pass

    Returns:
        int: Active bug count
    """
    from qa_status_utils import is_clickup_visible_bug

    print(f"📊 Counting active 2.0.0 bugs...")

    with open(BUGS_FILE, 'r', encoding='utf-8') as f:
        bugs = json.load(f)

    active_bugs = [
        bug for bug in bugs
        if is_clickup_visible_bug(bug)
    ]

    count = len(active_bugs)
    print(f"✅ Current active bugs: {count}")

    return count


def update_daily_actuals(count):
    """
    Add or update today's count in daily_actuals.json.

    IMPORTANT: Never modifies historical data (past dates).
    Only appends new dates or updates today's count.

    Args:
        count: Today's bug count

    Returns:
        bool: True if added new entry, False if updated existing
    """
    print(f"\n💾 Updating daily actuals...")

    # Load existing data
    with open(DAILY_ACTUALS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    today_str = TODAY.strftime('%Y-%m-%d')
    daily_counts = data['daily_counts']

    # Check if today already exists
    existing_index = next(
        (i for i, entry in enumerate(daily_counts) if entry['date'] == today_str),
        None
    )

    if existing_index is not None:
        # Update existing entry
        old_count = daily_counts[existing_index]['count']
        daily_counts[existing_index]['count'] = count
        daily_counts[existing_index]['source'] = 'clickup_live_count'
        daily_counts[existing_index]['updated'] = datetime.now().isoformat()

        print(f"📝 Updated {today_str}: {old_count} → {count}")
        is_new = False
    else:
        # Append new entry
        new_entry = {
            'date': today_str,
            'count': count,
            'source': 'clickup_live_count',
            'timestamp': datetime.now().isoformat()
        }
        daily_counts.append(new_entry)

        print(f"➕ Added {today_str}: {count} bugs")
        is_new = True

    # Save
    with open(DAILY_ACTUALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved to {DAILY_ACTUALS_FILE}")
    print(f"   Total historical records: {len(daily_counts)}")

    return is_new


def main():
    """Main execution."""
    print(f"\n{'='*60}")
    print(f"📅 Daily Actuals Update - {TODAY.strftime('%B %d, %Y')}")
    print(f"{'='*60}\n")

    # Step 1: Fetch and parse ClickUp data
    if not fetch_and_parse_clickup_data():
        print(f"\n❌ Failed to fetch ClickUp data")
        sys.exit(1)

    # Step 2: Count active bugs
    try:
        count = count_active_bugs()
    except FileNotFoundError:
        print(f"❌ Bug data file not found: {BUGS_FILE}")
        print(f"   This should have been created by parse_and_map_milestones.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error counting bugs: {e}")
        sys.exit(1)

    # Step 3: Update daily actuals
    try:
        is_new = update_daily_actuals(count)
    except FileNotFoundError:
        print(f"❌ Daily actuals file not found: {DAILY_ACTUALS_FILE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error updating daily actuals: {e}")
        sys.exit(1)

    # Summary
    print(f"\n{'='*60}")
    print(f"✅ Daily Actuals Updated!")
    print(f"{'='*60}")
    print(f"Date: {TODAY.strftime('%B %d, %Y')}")
    print(f"Count: {count} active bugs")
    print(f"Action: {'New entry added' if is_new else 'Existing entry updated'}")
    print(f"\n💡 Next step: Run dashboard generation scripts to update visualizations")


if __name__ == "__main__":
    main()
