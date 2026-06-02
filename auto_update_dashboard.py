#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Update Bug Burndown Dashboard

Automated script that:
1. Fetches latest bug data from ClickUp
2. Recalculates projections
3. Regenerates dashboard HTML
4. Updates Slack content
5. Commits and pushes to GitHub (auto-deploys GitHub Pages)

Designed to run 3x daily via cron/scheduled task.
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


def print_section(title):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def run_script(script_name, description):
    """
    Run a Python script and return success status.

    Args:
        script_name: Name of script to run
        description: Human-readable description

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"▶ {description}...")
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"   Error: {e.stderr[:200]}")
        return False
    except Exception as e:
        print(f"❌ {description} - Unexpected error: {e}")
        return False


def git_commit_and_push(message):
    """
    Commit changes and push to GitHub.

    Args:
        message: Commit message

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"▶ Committing and pushing to GitHub...")

    try:
        # Check if there are changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True
        )

        if not result.stdout.strip():
            print(f"ℹ️  No changes to commit")
            return True

        # Add files
        subprocess.run(
            ['git', 'add', 'docs/index.html', 'burndown_projections.json',
             'burndown_chart.png', 'slack_message.json'],
            check=True
        )

        # Commit
        subprocess.run(
            ['git', 'commit', '-m', message],
            check=True,
            capture_output=True
        )

        # Push
        subprocess.run(
            ['git', 'push'],
            check=True,
            capture_output=True
        )

        print(f"✅ Pushed to GitHub - Dashboard will update in 1-2 minutes")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        return False


def load_projections():
    """Load current projection data to get metrics."""
    try:
        with open('burndown_projections.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def main():
    """Main execution."""
    start_time = datetime.now()

    print("\n" + "🔄 " * 20)
    print_section("🤖 Automated Dashboard Update")
    print(f"Started: {start_time.strftime('%B %d, %Y at %I:%M %p')}")

    # Track success of each step
    steps = []

    # Step 1: Fetch latest bug data from ClickUp
    # Note: This would need to be implemented to update bugs_with_parsed_dates.json
    # For now, we'll assume the data is already current or manually updated
    print_section("📥 Step 1: Fetch Latest Bug Data")
    print("ℹ️  Skipping - Using existing bug data")
    print("   (TODO: Implement ClickUp API fetch to update bugs_with_parsed_dates.json)")
    steps.append(('Fetch Data', True))

    # Step 2: Recalculate projections
    print_section("📊 Step 2: Recalculate Projections")
    success = run_script(
        'calculate_burndown_projections.py',
        'Calculating burndown projections'
    )
    steps.append(('Calculate Projections', success))

    if not success:
        print("\n⚠️  Cannot continue without projections. Exiting.")
        sys.exit(1)

    # Step 3: Regenerate dashboard HTML
    print_section("🎨 Step 3: Regenerate Dashboard")
    success = run_script(
        'generate_burndown_projection_chart.py',
        'Generating dashboard HTML'
    )
    steps.append(('Generate Dashboard', success))

    # Step 4: Generate Slack content
    print_section("💬 Step 4: Generate Slack Content")
    success = run_script(
        'generate_slack_burndown.py',
        'Generating Slack chart and message'
    )
    steps.append(('Generate Slack Content', success))

    # Step 5: Commit and push to GitHub
    print_section("🚀 Step 5: Deploy to GitHub Pages")

    # Load metrics for commit message
    data = load_projections()
    if data:
        bugs = data['current_active_bugs']
        days = data.get('business_days_to_code_freeze', 0)
        commit_msg = f"Auto-update dashboard: {bugs} bugs, {days} days to Code Freeze\n\n{start_time.strftime('%Y-%m-%d %H:%M')}"
    else:
        commit_msg = f"Auto-update dashboard\n\n{start_time.strftime('%Y-%m-%d %H:%M')}"

    success = git_commit_and_push(commit_msg)
    steps.append(('Deploy to GitHub', success))

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print_section("📋 Summary")

    for step_name, step_success in steps:
        status = "✅" if step_success else "❌"
        print(f"{status} {step_name}")

    print(f"\n⏱️  Duration: {duration:.1f} seconds")
    print(f"🕐 Completed: {end_time.strftime('%I:%M %p')}")

    # Show current metrics
    if data:
        print(f"\n📊 Current Metrics:")
        print(f"   Active Bugs: {data['current_active_bugs']}")
        print(f"   Days to Code Freeze: {data.get('business_days_to_code_freeze', 0)}")
        print(f"   Required Rate: {data['ideal_rate_per_day']:.1f} bugs/day")
        print(f"   Estimated Rate: {data.get('estimated_line_rate', data['historical_daily_rate']):.2f} bugs/day")
        print(f"   Velocity Gap: {data['metrics']['velocity_gap']:.1f}x")

    # Check if all critical steps succeeded
    critical_steps = [s for s in steps if s[0] in ['Calculate Projections', 'Generate Dashboard', 'Deploy to GitHub']]
    all_critical_success = all(s[1] for s in critical_steps)

    if all_critical_success:
        print(f"\n✅ Update completed successfully!")
        print(f"🔗 Dashboard: https://taylorwestfall-12.github.io/Spire-2-0-burndown-/")
        sys.exit(0)
    else:
        print(f"\n⚠️  Update completed with errors. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
