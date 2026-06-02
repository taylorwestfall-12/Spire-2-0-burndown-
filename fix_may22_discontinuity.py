#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix May 22 Discontinuity

The issue: May 21 shows 159 bugs (from original historical data with NO QA filter),
but May 22 shows 30 bugs (from retroactive calculation WITH QA filter).

Solution: For May 22 - June 1, calculate using the SAME method as the original
historical data (no QA Status filter). Only apply QA Status exclusions to TODAY (June 2).
"""

import json
import sys
from datetime import datetime, timedelta

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BUGS_FILE = "spire_bugs_complete.json"
HISTORICAL_FILE = "historical_actuals_5_11_to_5_21.json"
OUTPUT_FILE = "complete_actuals_may11_jun02.json"
QA_STATUS_FIELD_ID = "67ea8f39-eef6-4786-bab9-61586a1a5814"

# QA Status values to exclude (only for June 2 onwards)
EXCLUDED_QA_STATUSES = [10, 11, 12, 13]  # Duplicated, Not a Bug, Won't Fix, QA Pass


def get_qa_status_value(bug):
    """Extract QA Status from bug custom fields."""
    custom_fields = bug.get('custom_fields', [])
    for field in custom_fields:
        if field.get('id') == QA_STATUS_FIELD_ID:
            return field.get('value')
    return None


def get_milestone(bug):
    """Extract milestone from bug custom fields."""
    custom_fields = bug.get('custom_fields', [])
    for field in custom_fields:
        if field.get('id') == '9a1361a8-e8e6-450e-9ad6-e81f7bb65261':
            value = field.get('value')
            if value is not None:
                options = field.get('type_config', {}).get('options', [])
                if isinstance(value, int) and value < len(options):
                    return options[value].get('name', 'Unknown')
    return 'Unknown'


def calculate_daily_counts(bugs, start_date, end_date, apply_qa_filter=False):
    """Calculate daily counts for date range."""
    print(f"📊 Calculating {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')} ({'with QA filter' if apply_qa_filter else 'NO QA filter'})...")

    milestone_2_0 = [b for b in bugs if get_milestone(b) == '2.0.0 Global']

    daily_counts = []
    current_date = start_date
    excluded_statuses = ['Closed', 'closed', "won't fix", "Won't Fix", "WON'T FIX"]

    while current_date <= end_date:
        start_of_day = current_date.replace(hour=0, minute=0, second=0)
        active_count = 0

        for bug in milestone_2_0:
            # Check main status
            status = bug.get('status', {}).get('status', '')
            if status in excluded_statuses:
                continue

            # Check dates
            date_created_ms = bug.get('date_created')
            date_closed_ms = bug.get('date_closed')

            if not date_created_ms:
                continue

            date_created = datetime.fromtimestamp(int(date_created_ms) / 1000)
            if date_created >= start_of_day:
                continue

            if date_closed_ms:
                date_closed = datetime.fromtimestamp(int(date_closed_ms) / 1000)
                if date_closed < start_of_day:
                    continue

            # Apply QA Status filter ONLY if requested (for June 2 only)
            if apply_qa_filter:
                qa_status = get_qa_status_value(bug)
                if qa_status in EXCLUDED_QA_STATUSES:
                    continue

            active_count += 1

        daily_counts.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': active_count
        })

        print(f"   {current_date.strftime('%Y-%m-%d')}: {active_count} bugs")
        current_date += timedelta(days=1)

    return daily_counts


def main():
    """Fix May 22 discontinuity."""
    print("🔧 Fixing May 22 Discontinuity\n")
    print("="*60)
    print("Strategy: Use consistent counting method May 11 - June 1")
    print("          Apply QA Status exclusions ONLY to June 2")
    print("="*60)

    # Load historical actuals (May 11-21)
    with open(HISTORICAL_FILE, 'r') as f:
        historical = json.load(f)
    historical_actuals = historical['actuals']
    print(f"\nLoaded historical: {historical_actuals[0]['date']} to {historical_actuals[-1]['date']}")
    print(f"  May 21 count: {historical_actuals[-1]['count']} bugs")

    # Load raw bugs
    with open(BUGS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    bugs = data['bugs']

    # Calculate May 22 - June 1 WITHOUT QA filter (same as historical method)
    print("\n")
    may22_jun1 = calculate_daily_counts(bugs, datetime(2026, 5, 22), datetime(2026, 6, 1), apply_qa_filter=False)

    # Calculate June 2 WITH QA filter
    print()
    june2 = calculate_daily_counts(bugs, datetime(2026, 6, 2), datetime(2026, 6, 2), apply_qa_filter=True)

    # Combine all
    complete_actuals = historical_actuals + may22_jun1 + june2

    print(f"\n✅ Checking for discontinuity:")
    print(f"   May 21: {historical_actuals[-1]['count']} bugs")
    print(f"   May 22: {may22_jun1[0]['count']} bugs (difference: {may22_jun1[0]['count'] - historical_actuals[-1]['count']:+d})")
    print(f"   June 2: {june2[0]['count']} bugs")

    # Save
    output = {
        'metadata': {
            'method': 'Consistent counting May 11-Jun 1 (no QA filter), QA Status exclusions only on Jun 2',
            'qa_status_exclusions_applied_from': '2026-06-02',
            'start_date': '2026-05-11',
            'end_date': '2026-06-02'
        },
        'actuals': complete_actuals
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Complete actuals saved!")
    print(f"   Start (May 11): {complete_actuals[0]['count']} bugs")
    print(f"   End (June 2): {complete_actuals[-1]['count']} bugs")
    print(f"   Total points: {len(complete_actuals)}")
    print("="*60)


if __name__ == "__main__":
    main()
