#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Duplicate Actual Data Points

Removes duplicate dates from the actual line in burndown_projections.json,
keeping only the first occurrence of each date (which has the correct values).
"""

import json
import sys
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

PROJECTIONS_FILE = "burndown_projections.json"


def fix_duplicate_actuals():
    """Remove duplicate dates from actual line, keeping first occurrence."""
    print("🔧 Fixing duplicate actual data points...")

    # Load projections
    with open(PROJECTIONS_FILE, 'r', encoding='utf-8') as f:
        projections = json.load(f)

    # Get actual line
    actual = projections['projections']['actual']

    print(f"   Before: {len(actual)} data points")

    # Remove duplicates, keeping first occurrence
    seen_dates = set()
    cleaned_actual = []

    for point in actual:
        date = point['date']
        if date not in seen_dates:
            seen_dates.add(date)
            cleaned_actual.append(point)
        else:
            print(f"   Removing duplicate: {date} (count: {point['count']})")

    # Sort by date to ensure chronological order
    cleaned_actual.sort(key=lambda p: datetime.fromisoformat(p['date']))

    print(f"   After: {len(cleaned_actual)} data points")

    # Update projections
    projections['projections']['actual'] = cleaned_actual

    # Save
    with open(PROJECTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(projections, f, indent=2)

    print(f"✅ Fixed! Saved to {PROJECTIONS_FILE}")

    # Show the cleaned data
    print("\n📊 Cleaned actual data:")
    for point in cleaned_actual[-5:]:  # Show last 5 points
        print(f"   {point['date']}: {point['count']} bugs")


if __name__ == "__main__":
    fix_duplicate_actuals()
