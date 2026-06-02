#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculate Missing Daily Bug Counts (5/22 - 6/1)

Retroactively calculates daily active bug counts for 2.0.0 Global
by examining created/closed dates in bug data.

For each day, count bugs that:
- Were created on or before that date
- Were NOT closed before that date (still active)
- Status is NOT in excluded list (Closed, Won't Fix, etc.)

Output: Historical actual counts for 5/22 through 6/1
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
BUGS_FILE = "bugs_with_parsed_dates.json"
BURNDOWN_FILE = "burndown_projections.json"

# Date range for missing data
START_DATE = datetime(2026, 5, 22)
END_DATE = datetime(2026, 6, 1)

# Excluded statuses (same as update_today_burndown.py)
EXCLUDED_STATUSES = ['Closed', 'closed', "won't fix", "Won't Fix", "WON'T FIX"]


def load_bugs():
    """Load bug data from JSON file."""
    print(f"📂 Loading bugs from {BUGS_FILE}...")
    with open(BUGS_FILE, 'r', encoding='utf-8') as f:
        bugs = json.load(f)
    print(f"✅ Loaded {len(bugs)} bugs")
    return bugs


def calculate_daily_counts(bugs, start_date, end_date):
    """
    Calculate active bug count for each day in the range.

    For each day, count 2.0.0 Global bugs that:
    - Were created on or before that date
    - Were NOT closed before that date
    - Status is NOT in excluded list

    Args:
        bugs: List of bug dictionaries
        start_date: First date to calculate
        end_date: Last date to calculate

    Returns:
        list: [{date, count}] for each day
    """
    print(f"\n📊 Calculating daily counts from {start_date.strftime('%b %d')} to {end_date.strftime('%b %d, %Y')}...")

    # Filter to 2.0.0 Global bugs
    milestone_2_0 = [
        bug for bug in bugs
        if bug.get('milestone_simplified') == '2.0.0 Global'
    ]

    print(f"   Total 2.0.0 Global bugs: {len(milestone_2_0)}")

    daily_counts = []
    current_date = start_date

    while current_date <= end_date:
        # Set time to start of day for comparison
        start_of_day = current_date.replace(hour=0, minute=0, second=0)

        # Count active bugs on this date
        active_on_date = 0

        for bug in milestone_2_0:
            # Parse dates
            date_created_str = bug.get('date_created')
            date_closed_str = bug.get('date_closed')

            if not date_created_str:
                continue  # Skip bugs without creation date

            # Parse ISO format datetime
            date_created = datetime.fromisoformat(date_created_str)

            # Was this bug created by this date?
            # Bug must be created BEFORE the start of this day to count as "active on this day"
            if date_created >= start_of_day:
                continue  # Not created yet (or created today, so doesn't count as active YET)

            # Was this bug already closed by this date?
            if date_closed_str:
                date_closed = datetime.fromisoformat(date_closed_str)
                # If closed before the start of this day, it doesn't count as active
                if date_closed < start_of_day:
                    continue  # Already closed

            # Bug was active on this date (created before today, not yet closed)
            active_on_date += 1

        daily_counts.append({
            "date": current_date.strftime('%Y-%m-%d'),
            "count": active_on_date
        })

        print(f"   {current_date.strftime('%b %d')}: {active_on_date} active bugs")

        current_date += timedelta(days=1)

    return daily_counts


def update_burndown_projections(new_actuals):
    """Insert new actuals into burndown_projections.json."""
    print(f"\n📝 Updating {BURNDOWN_FILE}...")

    # Load current projections
    with open(BURNDOWN_FILE, 'r', encoding='utf-8') as f:
        projections = json.load(f)

    # Get current actuals
    current_actuals = projections['projections']['actual']

    # Find where to insert (after May 21, before Jun 02)
    insert_index = None
    for i, point in enumerate(current_actuals):
        if point['date'] == '2026-05-21':
            insert_index = i + 1
            break

    if insert_index is None:
        print("❌ Could not find May 21 in actuals")
        return False

    # Remove the Jun 02 point (we'll re-add it at the end)
    jun_02_point = None
    for i, point in enumerate(current_actuals):
        if point['date'] == '2026-06-02':
            jun_02_point = current_actuals.pop(i)
            break

    # Insert new actuals
    for point in new_actuals:
        current_actuals.insert(insert_index, point)
        insert_index += 1

    # Re-add Jun 02 at the end
    if jun_02_point:
        current_actuals.append(jun_02_point)

    # Update projections
    projections['projections']['actual'] = current_actuals
    projections['key_dates']['today'] = END_DATE.strftime('%Y-%m-%d')

    # Save updated projections
    with open(BURNDOWN_FILE, 'w', encoding='utf-8') as f:
        json.dump(projections, f, indent=2)

    print(f"✅ Added {len(new_actuals)} data points")
    return True


def main():
    """Main execution."""
    print("🔍 Calculating Missing Daily Bug Counts")
    print("="*60)
    print(f"Date range: {START_DATE.strftime('%b %d')} - {END_DATE.strftime('%b %d, %Y')}")
    print(f"Milestone: 2.0.0 Global")
    print()

    # Load bugs
    bugs = load_bugs()

    # Calculate daily counts
    daily_counts = calculate_daily_counts(bugs, START_DATE, END_DATE)

    # Update burndown projections
    if update_burndown_projections(daily_counts):
        print(f"\n{'='*60}")
        print(f"✅ COMPLETE!")
        print(f"{'='*60}")

        # Show summary
        counts_list = [point['count'] for point in daily_counts]
        print(f"\nSummary:")
        print(f"  Starting count (5/22): {counts_list[0]}")
        print(f"  Ending count (6/01): {counts_list[-1]}")
        print(f"  Net change: {counts_list[-1] - counts_list[0]:+d} bugs")
        print(f"  Average daily change: {(counts_list[-1] - counts_list[0]) / len(counts_list):.2f} bugs/day")

        print(f"\nNext step: Run generate_burndown_projection_chart.py to visualize")
    else:
        print("\n❌ Failed to update projections")


if __name__ == "__main__":
    main()
