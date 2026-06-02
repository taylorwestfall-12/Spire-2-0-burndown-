#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recalculate Ideal Line

Updates the ideal projection line to start from the actual chart start bug count.
"""

import json
import sys
from datetime import datetime, timedelta

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

PROJECTIONS_FILE = "burndown_projections.json"
CHART_START = datetime(2026, 5, 11)
CODE_FREEZE = datetime(2026, 6, 4)


def count_business_days(start_date, end_date):
    """Count business days between two dates."""
    business_days = 0
    current = start_date
    while current < end_date:
        if current.weekday() < 5:  # Monday-Friday
            business_days += 1
        current += timedelta(days=1)
    return business_days


def generate_ideal_line(start_count, start_date, end_date):
    """Generate ideal line from start to zero by end date."""
    business_days = count_business_days(start_date, end_date)
    rate = -start_count / business_days if business_days > 0 else 0

    print(f"📊 Ideal Line Calculation:")
    print(f"   Start: {start_date.strftime('%b %d')} with {start_count} bugs")
    print(f"   Target: Zero bugs by {end_date.strftime('%b %d')}")
    print(f"   Business days: {business_days}")
    print(f"   Required rate: {rate:.2f} bugs/day")

    ideal_line = []
    current_date = start_date
    business_days_elapsed = 0
    last_business_day_count = start_count

    while current_date <= end_date:
        is_weekend = current_date.weekday() >= 5  # Saturday=5, Sunday=6

        if is_weekend:
            # Weekend: plateau
            ideal_line.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "count": last_business_day_count
            })
        else:
            # Business day: apply rate
            if business_days_elapsed == 0:
                # First day: use exact start count
                new_count = start_count
            else:
                new_count = start_count + (rate * business_days_elapsed)
                new_count = max(0, new_count)  # Never go negative

            business_days_elapsed += 1
            last_business_day_count = new_count

            ideal_line.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "count": new_count
            })

        current_date += timedelta(days=1)

    return ideal_line, rate


def main():
    """Recalculate ideal line."""
    print("🔄 Recalculating Ideal Line\n")
    print("="*60)

    # Load projections
    with open(PROJECTIONS_FILE, 'r', encoding='utf-8') as f:
        projections = json.load(f)

    # Get actual chart start count
    actual_line = projections['projections']['actual']
    chart_start_count = actual_line[0]['count']

    print(f"Chart start count: {chart_start_count} bugs (from actual data)")
    print()

    # Generate new ideal line
    ideal_line, ideal_rate = generate_ideal_line(chart_start_count, CHART_START, CODE_FREEZE)

    # Update projections
    projections['projections']['ideal'] = ideal_line
    projections['chart_start_bug_count'] = chart_start_count
    projections['ideal_rate_from_start'] = ideal_rate

    # Save
    with open(PROJECTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(projections, f, indent=2)

    print(f"\n✅ Updated ideal line!")
    print(f"   Start: {chart_start_count} bugs on {CHART_START.strftime('%b %d')}")
    print(f"   Rate: {ideal_rate:.2f} bugs/day")
    print(f"   Points: {len(ideal_line)}")
    print("="*60)


if __name__ == "__main__":
    main()
