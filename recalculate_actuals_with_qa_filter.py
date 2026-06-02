#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recalculate Complete Actual Data with QA Status Filter

Retroactively calculates daily active bug counts for May 11 - June 2
using ClickUp's QA Status filter logic.
"""

import json
import sys
from datetime import datetime, timedelta

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
BUGS_FILE = "spire_bugs_complete.json"
OUTPUT_FILE = "complete_actuals_may11_jun02.json"
QA_STATUS_FIELD_ID = "67ea8f39-eef6-4786-bab9-61586a1a5814"

# Date range
START_DATE = datetime(2026, 5, 11)
END_DATE = datetime(2026, 6, 2)

# QA Status values that count as "active" in ClickUp
ACTIVE_QA_STATUSES = [1, 4]  # QA Review, Open


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


def calculate_daily_counts():
    """Calculate daily counts with QA Status filter."""
    print("🔄 Recalculating Historical Actuals with QA Status Filter")
    print("="*60)
    print(f"Date range: {START_DATE.strftime('%b %d')} - {END_DATE.strftime('%b %d, %Y')}")
    print(f"Milestone: 2.0.0 Global")
    print(f"QA Status filter: QA Review (1) or Open (4)")
    print()

    # Load raw ClickUp data
    print(f"📂 Loading bugs from {BUGS_FILE}...")
    with open(BUGS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    bugs = data['bugs']
    print(f"✅ Loaded {len(bugs)} bugs")

    # Filter to 2.0.0 Global
    milestone_2_0 = []
    for bug in bugs:
        if get_milestone(bug) == '2.0.0 Global':
            milestone_2_0.append(bug)

    print(f"   2.0.0 Global bugs: {len(milestone_2_0)}")

    # Calculate daily counts
    print(f"\n📊 Calculating daily counts...")
    actuals = []
    current_date = START_DATE

    excluded_statuses = ['Closed', 'closed', "won't fix", "Won't Fix", "WON'T FIX"]

    while current_date <= END_DATE:
        start_of_day = current_date.replace(hour=0, minute=0, second=0)
        active_count = 0

        for bug in milestone_2_0:
            # Check status
            status = bug.get('status', {}).get('status', '')
            if status in excluded_statuses:
                continue

            # Check dates
            date_created_ms = bug.get('date_created')
            date_closed_ms = bug.get('date_closed')

            if not date_created_ms:
                continue

            # Convert to datetime
            date_created = datetime.fromtimestamp(int(date_created_ms) / 1000)

            # Bug must be created before this day
            if date_created >= start_of_day:
                continue

            # If closed, must be closed after this day starts
            if date_closed_ms:
                date_closed = datetime.fromtimestamp(int(date_closed_ms) / 1000)
                if date_closed < start_of_day:
                    continue

            # Check QA Status - this is the NEW filter
            qa_status = get_qa_status_value(bug)
            if qa_status not in ACTIVE_QA_STATUSES:
                continue  # Not "QA Review" or "Open"

            # Bug is active on this date
            active_count += 1

        actuals.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': active_count
        })

        print(f"   {current_date.strftime('%Y-%m-%d')}: {active_count} bugs")
        current_date += timedelta(days=1)

    # Save results
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    output = {
        'metadata': {
            'calculated_date': datetime.now().isoformat(),
            'method': 'Retroactive calculation with QA Status filter',
            'qa_status_filter': 'QA Review (1) or Open (4)',
            'start_date': START_DATE.strftime('%Y-%m-%d'),
            'end_date': END_DATE.strftime('%Y-%m-%d')
        },
        'actuals': actuals
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Saved {len(actuals)} daily counts")

    # Summary
    print(f"\n{'='*60}")
    print(f"✅ COMPLETE!")
    print(f"{'='*60}")
    print(f"\nSummary:")
    print(f"  Start ({START_DATE.strftime('%b %d')}): {actuals[0]['count']} bugs")
    print(f"  End ({END_DATE.strftime('%b %d')}): {actuals[-1]['count']} bugs")
    print(f"  Net change: {actuals[-1]['count'] - actuals[0]['count']:+d} bugs")
    print(f"  Average daily change: {(actuals[-1]['count'] - actuals[0]['count']) / len(actuals):.2f} bugs/day")
    print(f"\nOutput saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    calculate_daily_counts()
