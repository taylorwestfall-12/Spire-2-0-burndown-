#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Dashboard from Daily Actuals

Reads daily_actuals.json (source of truth) and:
1. Loads actual line data
2. Calculates ideal line (from start to Code Freeze)
3. Calculates estimated line (using last 10 business days rate)
4. Updates burndown_projections.json
5. Generates dashboard HTML
6. Generates Slack content

This replaces the old workflow that recalculated historical data.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
DAILY_ACTUALS_FILE = "daily_actuals.json"
MILESTONE_DATES_FILE = "milestone_dates_2.0.0.json"
PROJECTIONS_FILE = "burndown_projections.json"
HISTORICAL_RATE_FILE = "historical_rate_analysis.json"


def load_daily_actuals():
    """Load daily actuals from persistent file."""
    print("📂 Loading daily actuals...")

    with open(DAILY_ACTUALS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    actuals = [
        {'date': entry['date'], 'count': entry['count']}
        for entry in data['daily_counts']
    ]

    print(f"✅ Loaded {len(actuals)} daily records")
    print(f"   Range: {actuals[0]['date']} to {actuals[-1]['date']}")
    print(f"   Start: {actuals[0]['count']} bugs")
    print(f"   Current: {actuals[-1]['count']} bugs")

    return actuals


def calculate_business_days(start_date, end_date):
    """Calculate business days between two dates."""
    business_days = 0
    current = start_date

    while current <= end_date:
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            business_days += 1
        current += timedelta(days=1)

    return business_days


def calculate_estimated_line(actuals, go_live_date, historical_rate):
    """
    Calculate estimated line using last 10 business days rate.

    Args:
        actuals: List of actual data points
        go_live_date: Go live date
        historical_rate: Historical rate (fallback)

    Returns:
        tuple: (estimated_line, rate, rate_source)
    """
    print("\n📈 Calculating estimated line...")

    # Get last 10 business days
    business_days = []
    for entry in reversed(actuals):
        date = datetime.strptime(entry['date'], '%Y-%m-%d')
        if date.weekday() < 5:  # Business day
            business_days.append(entry)
        if len(business_days) == 10:
            break

    business_days.reverse()

    if len(business_days) >= 10:
        # Use actual milestone rate
        start_count = business_days[0]['count']
        end_count = business_days[-1]['count']
        rate = (end_count - start_count) / 10
        rate_source = "last 10 business days (actual milestone performance)"

        print(f"   Using last 10 business days:")
        print(f"   {business_days[0]['date']}: {start_count} bugs")
        print(f"   {business_days[-1]['date']}: {end_count} bugs")
        print(f"   Rate: {rate:.2f} bugs/day")
    else:
        # Fall back to historical
        rate = historical_rate
        rate_source = "historical average (insufficient actual data)"
        print(f"   Using historical rate: {rate:.2f} bugs/day")

    # Project from last actual point
    last_actual = actuals[-1]
    start_date = datetime.strptime(last_actual['date'], '%Y-%m-%d')
    start_count = last_actual['count']

    estimated_line = []
    estimated_line.append({
        'date': start_date.strftime('%Y-%m-%d'),
        'count': start_count
    })

    current_date = start_date + timedelta(days=1)
    business_days_elapsed = 0
    last_business_day_count = start_count

    while current_date <= go_live_date:
        is_weekend = current_date.weekday() >= 5

        if is_weekend:
            count = last_business_day_count
        else:
            business_days_elapsed += 1
            count = start_count + (rate * business_days_elapsed)
            last_business_day_count = count

        if count <= 0:
            estimated_line.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': 0
            })
            break

        estimated_line.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': round(count, 2)
        })

        current_date += timedelta(days=1)

    print(f"✅ Estimated line calculated ({len(estimated_line)} points)")

    return estimated_line, rate, rate_source


def calculate_ideal_line(actuals, code_freeze_date):
    """
    Calculate ideal line from chart start to Code Freeze.

    Args:
        actuals: Actual data points
        code_freeze_date: Code Freeze date

    Returns:
        list: Ideal line data points
    """
    print("\n📊 Calculating ideal line...")

    start_entry = actuals[0]
    start_date = datetime.strptime(start_entry['date'], '%Y-%m-%d')
    start_count = start_entry['count']

    business_days = calculate_business_days(start_date, code_freeze_date)
    ideal_rate = -start_count / business_days

    print(f"   Start: {start_date.strftime('%b %d')} with {start_count} bugs")
    print(f"   Target: Zero by {code_freeze_date.strftime('%b %d')}")
    print(f"   Business days: {business_days}")
    print(f"   Required rate: {ideal_rate:.2f} bugs/day")

    ideal_line = []
    current_date = start_date
    business_days_elapsed = 0
    last_business_day_count = start_count

    while current_date <= code_freeze_date:
        is_weekend = current_date.weekday() >= 5

        if is_weekend:
            count = last_business_day_count
        else:
            business_days_elapsed += 1
            count = start_count + (ideal_rate * business_days_elapsed)
            last_business_day_count = count

        if count <= 0:
            count = 0

        ideal_line.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': round(count, 2)
        })

        current_date += timedelta(days=1)

    print(f"✅ Ideal line calculated ({len(ideal_line)} points)")

    return ideal_line, ideal_rate


def main():
    """Main execution."""
    print(f"\n{'='*60}")
    print(f"🎨 Generate Dashboard from Daily Actuals")
    print(f"{'='*60}\n")

    # Load milestone dates
    with open(MILESTONE_DATES_FILE, 'r') as f:
        milestone_data = json.load(f)

    milestone_dates = milestone_data['2.0.0_Global']['key_dates']
    code_freeze_date = datetime.strptime(milestone_dates['code_freeze'], '%Y-%m-%d')
    go_live_date = datetime.strptime(milestone_dates['go_live'], '%Y-%m-%d')
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Load historical rate
    with open(HISTORICAL_RATE_FILE, 'r') as f:
        historical_data = json.load(f)
    historical_rate = historical_data['historical_daily_rate']

    # Load daily actuals
    actuals = load_daily_actuals()

    # Calculate ideal line
    ideal_line, ideal_rate = calculate_ideal_line(actuals, code_freeze_date)

    # Calculate estimated line
    estimated_line, estimated_rate, rate_source = calculate_estimated_line(
        actuals, go_live_date, historical_rate
    )

    # Calculate metrics
    current_bugs = actuals[-1]['count']
    business_days_to_freeze = calculate_business_days(today, code_freeze_date)
    required_rate = -current_bugs / business_days_to_freeze if business_days_to_freeze > 0 else 0

    # Build projections
    projections = {
        'generated_date': today.strftime('%Y-%m-%d'),
        'generated_timestamp': datetime.now().isoformat(),
        'chart_start_date': actuals[0]['date'],
        'chart_start_bug_count': actuals[0]['count'],
        'current_active_bugs': current_bugs,
        'historical_daily_rate': historical_rate,
        'ideal_rate_per_day': required_rate,
        'ideal_rate_from_start': ideal_rate,
        'estimated_line_rate': estimated_rate,
        'estimated_line_rate_source': rate_source,
        'business_days_to_code_freeze': business_days_to_freeze,
        'calendar_days_to_code_freeze': (code_freeze_date - today).days,
        'days_to_go_live': (go_live_date - today).days,
        'key_dates': {
            'chart_start': actuals[0]['date'],
            'today': today.strftime('%Y-%m-%d'),
            'code_freeze': milestone_dates['code_freeze'],
            'submit': milestone_dates['submit'],
            'go_live': milestone_dates['go_live']
        },
        'projections': {
            'ideal': ideal_line,
            'estimated': estimated_line,
            'actual': actuals
        },
        'metrics': {
            'velocity_gap': abs(required_rate / estimated_rate) if estimated_rate != 0 else 0,
            'on_track': estimated_rate <= required_rate if estimated_rate < 0 else False
        }
    }

    # Save projections
    print(f"\n💾 Saving projections...")
    with open(PROJECTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(projections, f, indent=2)
    print(f"✅ Saved to {PROJECTIONS_FILE}")

    # Generate dashboard HTML
    print(f"\n🎨 Generating dashboard...")
    try:
        subprocess.run(
            [sys.executable, 'generate_burndown_projection_chart.py'],
            check=True,
            capture_output=True
        )
        print(f"✅ Dashboard generated")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Dashboard generation had issues")

    # Generate Slack content
    print(f"\n💬 Generating Slack content...")
    try:
        subprocess.run(
            [sys.executable, 'generate_slack_burndown.py'],
            check=True,
            capture_output=True
        )
        print(f"✅ Slack content generated")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Slack content generation had issues")

    # Summary
    print(f"\n{'='*60}")
    print(f"✅ Dashboard Generation Complete!")
    print(f"{'='*60}")
    print(f"Active Bugs: {current_bugs}")
    print(f"Days to Code Freeze: {business_days_to_freeze}")
    print(f"Required Rate: {required_rate:.2f} bugs/day")
    print(f"Estimated Rate: {estimated_rate:.2f} bugs/day")
    print(f"\n🔗 Dashboard: https://taylorwestfall-12.github.io/Spire-2-0-burndown-/")


if __name__ == "__main__":
    main()
