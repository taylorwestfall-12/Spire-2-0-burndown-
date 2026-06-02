#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smooth Missing Dates (May 22 - June 1)

Since we can't reliably retroactively calculate May 22 - June 1 data,
we'll interpolate between May 21 (159 bugs) and June 2 (46 bugs)
to show a smooth trend line.
"""

import json
import sys
from datetime import datetime, timedelta

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

HISTORICAL_FILE = "historical_actuals_5_11_to_5_21.json"
OUTPUT_FILE = "complete_actuals_may11_jun02.json"

# Known endpoints
MAY_21_COUNT = 159  # Last reliable historical data
JUNE_2_COUNT = 46   # Today's actual count (with QA filter)

# Date range to interpolate
START_DATE = datetime(2026, 5, 22)
END_DATE = datetime(2026, 6, 1)


def interpolate_dates():
    """Interpolate bug counts between May 21 and June 2."""
    print("📊 Interpolating May 22 - June 1 data\n")
    print("="*60)
    print(f"Known data points:")
    print(f"  May 21: {MAY_21_COUNT} bugs (last historical)")
    print(f"  June 2: {JUNE_2_COUNT} bugs (today's count)")
    print(f"\nInterpolating {(END_DATE - START_DATE).days + 1} days between them...")
    print("="*60)

    # Load historical data
    with open(HISTORICAL_FILE, 'r') as f:
        historical = json.load(f)

    historical_actuals = historical['actuals']

    # Calculate total days and daily change
    total_days = (datetime(2026, 6, 2) - datetime(2026, 5, 21)).days
    total_change = JUNE_2_COUNT - MAY_21_COUNT
    daily_change = total_change / total_days

    print(f"\nInterpolation calculation:")
    print(f"  Total change: {total_change} bugs over {total_days} days")
    print(f"  Daily change: {daily_change:.2f} bugs/day")

    # Interpolate each day
    interpolated = []
    current_date = START_DATE
    days_since_may21 = 1

    print(f"\nInterpolated values:")
    while current_date <= END_DATE:
        # Linear interpolation
        interpolated_count = MAY_21_COUNT + (daily_change * days_since_may21)
        interpolated_count = round(interpolated_count)

        interpolated.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': interpolated_count
        })

        print(f"  {current_date.strftime('%Y-%m-%d')}: {interpolated_count} bugs")

        current_date += timedelta(days=1)
        days_since_may21 += 1

    # Add June 2 (actual count)
    june_2_data = {
        'date': '2026-06-02',
        'count': JUNE_2_COUNT
    }

    print(f"  2026-06-02: {JUNE_2_COUNT} bugs (actual)")

    # Combine all data
    complete_actuals = historical_actuals + interpolated + [june_2_data]

    # Save
    output = {
        'metadata': {
            'method': 'Historical May 11-21 + Interpolated May 22-Jun 1 + Actual Jun 2',
            'note': 'May 22-Jun 1 interpolated linearly between May 21 (159) and Jun 2 (46)',
            'qa_status_exclusions': 'Applied to June 2 only (Won\'t Fix, Not a Bug, Duplicated, QA Pass)',
            'start_date': '2026-05-11',
            'end_date': '2026-06-02'
        },
        'actuals': complete_actuals
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Complete actuals saved!")
    print(f"   Total points: {len(complete_actuals)}")
    print(f"   May 21 → May 22 transition: {MAY_21_COUNT} → {interpolated[0]['count']} bugs")
    print("="*60)


if __name__ == "__main__":
    interpolate_dates()
