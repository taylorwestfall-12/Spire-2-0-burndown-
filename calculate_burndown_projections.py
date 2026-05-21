#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculate 2.0.0 Bug Burndown Projections

Generates three projection lines for 2.0.0 Global bugs:
1. Ideal: Linear decrease to zero by Code Freeze (June 2)
2. Estimated: Projection based on historical 6-month find vs fix rate
3. Actual: Current reality (starts with today, updates daily)

Output: burndown_projections.json
"""

import json
from datetime import datetime, timedelta
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
BUGS_FILE = "bugs_with_parsed_dates.json"
HISTORICAL_RATE_FILE = "historical_rate_analysis.json"
HISTORICAL_ACTUALS_FILE = "historical_actuals_5_11_to_5_21.json"
OUTPUT_FILE = "burndown_projections.json"

# Key Dates
CHART_START = datetime(2026, 5, 11)  # Chart starts from May 11
TODAY = datetime(2026, 5, 21)
CODE_FREEZE = datetime(2026, 6, 2)
SUBMIT = datetime(2026, 6, 10)
GO_LIVE = datetime(2026, 6, 15)

# Calculate business days to key milestones
def count_business_days(start_date, end_date):
    """Count business days (Mon-Fri) between two dates."""
    business_days = 0
    current = start_date
    while current < end_date:
        if current.weekday() < 5:  # Monday=0, Sunday=6
            business_days += 1
        current += timedelta(days=1)
    return business_days

# Days to key milestones (business days)
BUSINESS_DAYS_TO_CODE_FREEZE = count_business_days(TODAY, CODE_FREEZE)
DAYS_TO_GO_LIVE = (GO_LIVE - TODAY).days  # Keep calendar days for total projection length


def load_bug_data():
    """Load bug data from JSON file."""
    print(f"📂 Loading bug data from {BUGS_FILE}...")
    with open(BUGS_FILE, 'r', encoding='utf-8') as f:
        bugs = json.load(f)
    print(f"✅ Loaded {len(bugs)} bugs")
    return bugs


def load_historical_rate():
    """Load historical rate from analysis file."""
    print(f"📂 Loading historical rate from {HISTORICAL_RATE_FILE}...")
    with open(HISTORICAL_RATE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✅ Loaded historical rate: {data['historical_daily_rate']:.2f} bugs/day")
    return data


def load_historical_actuals():
    """Load historical actual bug counts from 5/11 to 5/21."""
    print(f"📂 Loading historical actuals from {HISTORICAL_ACTUALS_FILE}...")
    try:
        with open(HISTORICAL_ACTUALS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        actuals = data['actuals']
        print(f"✅ Loaded {len(actuals)} historical actual data points (5/11 - 5/21)")
        return actuals
    except FileNotFoundError:
        print(f"⚠️  Historical actuals file not found, will start from today only")
        return None


def count_active_2_0_bugs(bugs):
    """
    Count current active 2.0.0 Global bugs (non-Closed status, excluding WON'T FIX).

    Args:
        bugs: List of parsed bug dictionaries

    Returns:
        int: Count of active bugs
    """
    # Exclude both Closed and WON'T FIX statuses
    excluded_statuses = ['Closed', 'closed', "won't fix", "Won't Fix", "WON'T FIX"]

    active_bugs = [
        bug for bug in bugs
        if bug.get('milestone_simplified') == '2.0.0 Global'
        and bug.get('status') not in excluded_statuses
    ]

    print(f"\n📊 2.0.0 Global Bug Analysis:")
    print(f"   Total 2.0.0 bugs: {len([b for b in bugs if b.get('milestone_simplified') == '2.0.0 Global'])}")
    print(f"   Active (non-Closed): {len(active_bugs)}")

    # Show status breakdown
    status_counts = {}
    for bug in active_bugs:
        status = bug.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"\n   Status breakdown:")
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"     - {status}: {count}")

    return len(active_bugs)


def calculate_actual_2_0_rate(bugs):
    """
    Calculate actual rate for 2.0.0 bugs specifically.

    Measures fix vs find rate for 2.0.0 Global bugs in the current period.
    Uses same methodology as historical rate but only for 2.0.0 milestone.

    Args:
        bugs: List of parsed bug dictionaries

    Returns:
        float: Daily net rate for 2.0.0 bugs
    """
    # Get all 2.0.0 bugs
    milestone_2_0 = [b for b in bugs if b.get('milestone_simplified') == '2.0.0 Global']

    # Assume milestone started around 2026-04-28 (after 1.9.0 shipped)
    # Calculate through today (May 21)
    milestone_start = datetime(2026, 4, 28)
    milestone_end = TODAY
    days_in_period = (milestone_end - milestone_start).days

    # Bugs found during this period
    bugs_found = []
    for bug in milestone_2_0:
        if bug.get('date_created'):
            created = datetime.fromisoformat(bug['date_created'])
            if milestone_start <= created <= milestone_end:
                bugs_found.append(bug)

    # Bugs fixed (currently Closed)
    bugs_fixed = [b for b in milestone_2_0 if b.get('status') == 'Closed']

    # Net bugs removed
    net_bugs_removed = len(bugs_fixed) - len(bugs_found)

    # Daily rate
    actual_rate = net_bugs_removed / days_in_period if days_in_period > 0 else 0

    print(f"\n📊 Actual 2.0.0 Rate Calculation:")
    print(f"   Period: {milestone_start.strftime('%b %d')} to {milestone_end.strftime('%b %d, %Y')} ({days_in_period} days)")
    print(f"   Bugs found in period: {len(bugs_found)}")
    print(f"   Bugs fixed (Closed): {len(bugs_fixed)}")
    print(f"   Net bugs removed: {net_bugs_removed:+d}")
    print(f"   Actual daily rate: {actual_rate:+.2f} bugs/day")

    if actual_rate > 0:
        print(f"   ✅ Burning down (fixing faster than finding)")
    elif actual_rate < 0:
        print(f"   ⚠️  Accumulating (finding faster than fixing)")
    else:
        print(f"   ➖ Stable (no net change)")

    return actual_rate




def generate_ideal_line(chart_start_count, chart_start_date, code_freeze_date, business_days_from_start_to_freeze):
    """
    Generate Ideal projection line: Linear decrease to zero by Code Freeze.

    Starts from chart start date (May 11) with the historical count at that time,
    and shows linear path to zero by Code Freeze. Stops at Code Freeze (no line continuation).

    Args:
        chart_start_count: Bug count at chart start (e.g., 201 on May 11)
        chart_start_date: Start date for chart (e.g., May 11)
        code_freeze_date: Code Freeze date (target zero)
        business_days_from_start_to_freeze: Business days from chart start to Code Freeze

    Returns:
        tuple: (ideal_line list, ideal_rate_per_day)
    """
    # Calculate ideal rate based on BUSINESS days from chart start to Code Freeze
    ideal_rate_per_day = -chart_start_count / business_days_from_start_to_freeze

    print(f"\n📉 Ideal Line Calculation:")
    print(f"   Starting: {chart_start_date.strftime('%B %d, %Y')} with {chart_start_count} bugs")
    print(f"   Target: Zero bugs by {code_freeze_date.strftime('%B %d, %Y')}")
    print(f"   Business days to Code Freeze: {business_days_from_start_to_freeze}")
    print(f"   Required rate: {ideal_rate_per_day:.2f} bugs/day")

    ideal_line = []
    current_date = chart_start_date
    business_days_elapsed = 0
    last_business_day_count = chart_start_count

    # Generate line from chart start until it reaches zero or Code Freeze
    while current_date <= code_freeze_date:
        is_weekend = current_date.weekday() >= 5  # Saturday=5, Sunday=6

        if is_weekend:
            # Weekend: plateau at last business day's count
            count = last_business_day_count
        else:
            # Business day: calculate progress
            count = chart_start_count + (ideal_rate_per_day * business_days_elapsed)
            last_business_day_count = count
            business_days_elapsed += 1

        # If count would go negative, set to 0 and stop
        if count <= 0:
            ideal_line.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "count": 0
            })
            print(f"   Ideal line reaches zero on {current_date.strftime('%B %d, %Y')}")
            break  # Stop rendering after reaching zero

        ideal_line.append({
            "date": current_date.strftime('%Y-%m-%d'),
            "count": round(count, 2)
        })

        current_date += timedelta(days=1)

    return ideal_line, ideal_rate_per_day


def calculate_rate_from_actual_data(actual_line_data):
    """
    Calculate burndown rate from last 10 business days of actual data.

    Args:
        actual_line_data: List of actual data points

    Returns:
        float: Daily rate from last 10 business days, or None if not enough data
    """
    from datetime import datetime

    # Count business days in actual data
    business_days_data = []
    for i, point in enumerate(actual_line_data):
        date = datetime.strptime(point['date'], '%Y-%m-%d')
        if date.weekday() < 5:  # Monday=0, Friday=4
            business_days_data.append({
                'date': date,
                'count': point['count'],
                'index': i
            })

    total_business_days = len(business_days_data)

    print(f"\n📊 Actual Data Rate Calculation:")
    print(f"   Total actual data points: {len(actual_line_data)}")
    print(f"   Business days in actual data: {total_business_days}")

    # Need at least 10 business days to calculate
    if total_business_days < 10:
        print(f"   ⚠️  Not enough business days (<10), using historical rate")
        return None

    # Get last 10 business days
    last_10 = business_days_data[-10:]
    start_count = last_10[0]['count']
    end_count = last_10[-1]['count']
    net_change = end_count - start_count
    rate = net_change / 10

    print(f"   ✅ Using last 10 business days of actual data:")
    print(f"      Start: {last_10[0]['date'].strftime('%b %d')} = {start_count} bugs")
    print(f"      End: {last_10[-1]['date'].strftime('%b %d')} = {end_count} bugs")
    print(f"      Net change: {net_change:+.0f} bugs over 10 business days")
    print(f"      Calculated rate: {rate:+.2f} bugs/day")

    return rate


def generate_estimated_line(actual_line_data, end_date, historical_rate):
    """
    Generate Estimated projection line: Starts from last actual data point.

    Projects forward from the last actual data point using either:
    - Historical rate (if < 10 business days of actual data)
    - Rate calculated from last 10 business days (if >= 10 business days)

    Args:
        actual_line_data: List of actual data points
        end_date: Final date for projection (Go Live)
        historical_rate: Historical daily net rate (fallback)

    Returns:
        tuple: (estimated_line, rate_used, rate_source)
            - estimated_line: List of {"date": "YYYY-MM-DD", "count": float} dictionaries
            - rate_used: The rate used for projection (float)
            - rate_source: Description of rate source (string)
    """
    # Get last actual point as starting point for estimated line
    last_actual = actual_line_data[-1]
    start_count = last_actual['count']
    start_date = datetime.strptime(last_actual['date'], '%Y-%m-%d')

    # Try to calculate rate from actual data
    actual_rate = calculate_rate_from_actual_data(actual_line_data)

    # Use actual rate if available, otherwise fall back to historical
    rate = actual_rate if actual_rate is not None else historical_rate
    rate_source = "last 10 business days" if actual_rate is not None else "historical average"

    print(f"\n📊 Estimated Line Calculation:")
    print(f"   Starting: {start_date.strftime('%b %d')} with {start_count} bugs (last actual point)")
    print(f"   Rate: {rate:.2f} bugs/day ({rate_source})")

    estimated_line = []

    # Include the last actual point as first point to create seamless connection
    estimated_line.append({
        "date": start_date.strftime('%Y-%m-%d'),
        "count": start_count
    })

    current_date = start_date + timedelta(days=1)  # Continue from day after
    business_days_elapsed = 0
    last_business_day_count = start_count

    while current_date <= end_date:
        is_weekend = current_date.weekday() >= 5  # Saturday=5, Sunday=6

        if is_weekend:
            # Weekend: plateau at last business day's count
            count = last_business_day_count
        else:
            # Business day: calculate progress
            business_days_elapsed += 1
            count = start_count + (rate * business_days_elapsed)
            last_business_day_count = count

        # If count would go negative, set to 0 and stop
        if count <= 0:
            estimated_line.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "count": 0
            })
            print(f"   Estimated line reaches zero on {current_date.strftime('%B %d, %Y')}")
            break  # Stop rendering after reaching zero

        estimated_line.append({
            "date": current_date.strftime('%Y-%m-%d'),
            "count": round(count, 2)
        })

        current_date += timedelta(days=1)

    # If line never reached zero, report it
    if current_date > end_date and count > 0:
        print(f"   ⚠️  Projected to never reach zero within projection window")

    return estimated_line, rate, rate_source


def generate_actual_line(historical_actuals, starting_count, today):
    """
    Generate Actual line: Uses historical actuals from 5/11-5/21, will be updated daily.

    Args:
        historical_actuals: List of historical actual data points (or None)
        starting_count: Current active bug count (as of today)
        today: Today's date

    Returns:
        list: List of {"date": "YYYY-MM-DD", "count": int} dictionaries
    """
    print(f"\n✅ Actual Line:")

    if historical_actuals:
        # Use historical actuals from 5/11 through 5/21
        print(f"   Using historical actuals: {len(historical_actuals)} data points (5/11 - 5/21)")
        print(f"   Starting: {historical_actuals[0]['count']} bugs on {historical_actuals[0]['date']}")
        print(f"   Current: {historical_actuals[-1]['count']} bugs on {historical_actuals[-1]['date']}")
        return historical_actuals
    else:
        # Fallback: just use today's count
        print(f"   Starting point: {starting_count} bugs on {today.strftime('%B %d, %Y')}")
        print(f"   (Will be updated daily with real data)")
        return [{
            "date": today.strftime('%Y-%m-%d'),
            "count": starting_count
        }]


def save_projections(projections, output_file):
    """Save projection data to JSON file."""
    print(f"\n💾 Saving projections to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(projections, f, indent=2)
    print(f"✅ Saved successfully!")


def main():
    """Main execution function."""
    print("🚀 Calculating 2.0.0 Bug Burndown Projections")
    print("="*60)

    # Load data
    bugs = load_bug_data()
    historical_rate_data = load_historical_rate()
    historical_actuals = load_historical_actuals()

    # Calculate current active count
    active_count = count_active_2_0_bugs(bugs)

    # Get historical rate from analysis (for reference)
    historical_rate = historical_rate_data['historical_daily_rate']

    # Calculate actual rate for 2.0.0 bugs specifically
    actual_2_0_rate = calculate_actual_2_0_rate(bugs)

    # Get chart start count from historical actuals
    chart_start_count = historical_actuals[0]['count'] if historical_actuals else active_count

    # Calculate business days from chart start to Code Freeze
    business_days_from_start_to_freeze = count_business_days(CHART_START, CODE_FREEZE)

    print(f"\n📊 Chart Configuration:")
    print(f"   Chart starts: {CHART_START.strftime('%b %d')} with {chart_start_count} bugs")
    print(f"   Today: {TODAY.strftime('%b %d')} with {active_count} bugs")
    print(f"   Business days from start to Code Freeze: {business_days_from_start_to_freeze}")
    print(f"   Business days from today to Code Freeze: {BUSINESS_DAYS_TO_CODE_FREEZE}")

    # Generate actual line first (needed for estimated line)
    actual_line = generate_actual_line(historical_actuals, active_count, TODAY)

    # Generate projection lines
    ideal_line, ideal_rate_from_start = generate_ideal_line(
        chart_start_count, CHART_START, CODE_FREEZE, business_days_from_start_to_freeze
    )

    # Also calculate the rate required FROM TODAY (for dashboard metrics)
    ideal_rate_from_today = -active_count / BUSINESS_DAYS_TO_CODE_FREEZE

    # Generate estimated line starting from last actual point
    estimated_line, estimated_line_rate, estimated_line_rate_source = generate_estimated_line(
        actual_line, GO_LIVE, historical_rate
    )

    print(f"\n📊 Rate Comparison:")
    print(f"   Ideal rate from chart start (5/11): {ideal_rate_from_start:.2f} bugs/day")
    print(f"   Ideal rate from today (5/21): {ideal_rate_from_today:.2f} bugs/day (what's needed NOW)")

    # Build output structure
    projections = {
        "generated_date": TODAY.strftime('%Y-%m-%d'),
        "generated_timestamp": datetime.now().isoformat(),
        "chart_start_date": CHART_START.strftime('%Y-%m-%d'),
        "chart_start_bug_count": chart_start_count,
        "current_active_bugs": active_count,
        "historical_daily_rate": round(historical_rate, 2),  # Kept for reference
        "actual_2_0_rate": round(actual_2_0_rate, 2),  # Actual rate for 2.0.0 bugs
        "ideal_rate_per_day": round(ideal_rate_from_today, 2),  # Required rate from TODAY
        "ideal_rate_from_start": round(ideal_rate_from_start, 2),  # Rate from chart start (for line)
        "estimated_line_rate": round(estimated_line_rate, 2),  # Rate used for estimated line
        "estimated_line_rate_source": estimated_line_rate_source,  # Source of estimated rate
        "business_days_to_code_freeze": BUSINESS_DAYS_TO_CODE_FREEZE,  # Business days from TODAY
        "calendar_days_to_code_freeze": (CODE_FREEZE - TODAY).days,  # Calendar days for reference
        "days_to_go_live": DAYS_TO_GO_LIVE,
        "key_dates": {
            "chart_start": CHART_START.strftime('%Y-%m-%d'),
            "today": TODAY.strftime('%Y-%m-%d'),
            "code_freeze": CODE_FREEZE.strftime('%Y-%m-%d'),
            "submit": SUBMIT.strftime('%Y-%m-%d'),
            "go_live": GO_LIVE.strftime('%Y-%m-%d')
        },
        "projections": {
            "ideal": ideal_line,
            "estimated": estimated_line,
            "actual": actual_line
        },
        "metrics": {
            "velocity_gap": round(abs(ideal_rate_from_today / actual_2_0_rate), 2) if actual_2_0_rate != 0 else float('inf'),
            "on_track": actual_2_0_rate > abs(ideal_rate_from_today)
        }
    }

    # Save to file
    save_projections(projections, OUTPUT_FILE)

    # Print summary
    print("\n" + "="*60)
    print("📊 PROJECTION SUMMARY")
    print("="*60)
    print(f"Chart Start ({CHART_START.strftime('%b %d')}): {chart_start_count} bugs")
    print(f"Current Active Bugs ({TODAY.strftime('%b %d')}): {active_count}")
    print(f"Business Days to Code Freeze: {BUSINESS_DAYS_TO_CODE_FREEZE}")
    print(f"\nRequired Rate from TODAY: {ideal_rate_from_today:.2f} bugs/day")
    print(f"Actual 2.0.0 Rate: {actual_2_0_rate:+.2f} bugs/day")
    print(f"Historical Rate (reference): {historical_rate:.2f} bugs/day")

    if actual_2_0_rate != 0:
        velocity_gap = abs(ideal_rate_from_today / actual_2_0_rate)
        print(f"\nVelocity Gap: {velocity_gap:.1f}x improvement needed")
        if actual_2_0_rate > abs(ideal_rate_from_today):
            print(f"✅ On track to hit Code Freeze target!")
        else:
            print(f"⚠️  Need to accelerate to hit Code Freeze target")
    else:
        print(f"⚠️  Actual rate is zero (stable, no net change)")

    print(f"\nProjections saved to: {OUTPUT_FILE}")
    print("✅ Ready to generate dashboard!")


if __name__ == "__main__":
    main()
