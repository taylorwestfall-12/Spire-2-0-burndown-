#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recalculate Estimated Line Only

Updates the estimated projection line based on actual data,
without touching the actual line data.
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
GO_LIVE = datetime(2026, 6, 15)


def calculate_rate_from_actual_data(actual_line_data):
    """Calculate rate from last 10 business days."""
    # Count business days
    business_days_data = []
    for point in actual_line_data:
        date = datetime.strptime(point['date'], '%Y-%m-%d')
        if date.weekday() < 5:  # Monday-Friday
            business_days_data.append({
                'date': date,
                'count': point['count']
            })

    total_business_days = len(business_days_data)
    print(f"📊 Actual Data Rate Calculation:")
    print(f"   Total actual data points: {len(actual_line_data)}")
    print(f"   Business days in actual data: {total_business_days}")

    # Need at least 10 business days
    if total_business_days < 10:
        print(f"   ⚠️  Not enough business days (<10)")
        return None, "historical average"

    # Get last 10 business days
    last_10 = business_days_data[-10:]
    start_count = last_10[0]['count']
    end_count = last_10[-1]['count']
    net_change = end_count - start_count
    rate = net_change / 10

    print(f"   ✅ Using last 10 business days:")
    print(f"      {last_10[0]['date'].strftime('%b %d')} = {start_count} bugs")
    print(f"      {last_10[-1]['date'].strftime('%b %d')} = {end_count} bugs")
    print(f"      Net change: {net_change:+.0f} bugs over 10 days")
    print(f"      Rate: {rate:+.2f} bugs/day")

    return rate, "last 10 business days (actual milestone performance)"


def generate_estimated_line(actual_line_data, rate, rate_source):
    """Generate estimated line from last actual point."""
    # Get last actual point
    last_actual = actual_line_data[-1]
    start_count = last_actual['count']
    start_date = datetime.strptime(last_actual['date'], '%Y-%m-%d')

    print(f"\n📊 Estimated Line Calculation:")
    print(f"   Starting: {start_date.strftime('%b %d')} with {start_count} bugs (last actual point)")
    print(f"   Rate: {rate:.2f} bugs/day ({rate_source})")

    estimated_line = []

    # Start from the last actual point
    estimated_line.append({
        "date": start_date.strftime('%Y-%m-%d'),
        "count": start_count
    })

    current_date = start_date + timedelta(days=1)
    business_days_elapsed = 0
    last_business_day_count = start_count

    while current_date <= GO_LIVE:
        is_weekend = current_date.weekday() >= 5  # Saturday=5, Sunday=6

        if is_weekend:
            # Weekend: plateau at last business day count
            estimated_line.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "count": last_business_day_count
            })
        else:
            # Business day: apply rate
            business_days_elapsed += 1
            new_count = start_count + (rate * business_days_elapsed)
            new_count = max(0, new_count)  # Never go negative
            last_business_day_count = new_count

            estimated_line.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "count": new_count
            })

        current_date += timedelta(days=1)

    return estimated_line


def main():
    """Recalculate estimated line."""
    print("🔄 Recalculating Estimated Line\n")
    print("="*60)

    # Load projections
    with open(PROJECTIONS_FILE, 'r', encoding='utf-8') as f:
        projections = json.load(f)

    # Get actual line data
    actual_line = projections['projections']['actual']
    historical_rate = projections.get('historical_daily_rate', -3.8)

    # Calculate rate from actual data
    actual_rate, rate_source = calculate_rate_from_actual_data(actual_line)

    # Use actual rate if available, else historical
    rate = actual_rate if actual_rate is not None else historical_rate
    if actual_rate is None:
        rate_source = "historical average"

    # Generate new estimated line
    estimated_line = generate_estimated_line(actual_line, rate, rate_source)

    # Update projections
    projections['projections']['estimated'] = estimated_line
    projections['estimated_line_rate'] = rate
    projections['estimated_line_rate_source'] = rate_source

    # Save
    with open(PROJECTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(projections, f, indent=2)

    print(f"\n✅ Updated estimated line!")
    print(f"   Rate used: {rate:.2f} bugs/day")
    print(f"   Source: {rate_source}")
    print(f"   Points: {len(estimated_line)}")
    print(f"   Projected bugs on Go Live: {estimated_line[-1]['count']:.1f}")
    print("="*60)


if __name__ == "__main__":
    main()
