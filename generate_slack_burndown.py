#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Slack-Friendly Burndown Update

Creates a static PNG chart and formatted Slack message with key metrics.
Output: burndown_chart.png + slack_message.json (formatted for Slack Block Kit)
"""

import json
from datetime import datetime
import plotly.graph_objects as go
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
PROJECTIONS_FILE = "burndown_projections.json"
OUTPUT_IMAGE = "burndown_chart.png"
OUTPUT_MESSAGE = "slack_message.json"


def load_projections():
    """Load projection data from JSON file."""
    print(f"📂 Loading projection data from {PROJECTIONS_FILE}...")
    with open(PROJECTIONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✅ Loaded projections")
    return data


def create_chart_image(data):
    """
    Create static PNG chart for Slack.

    Args:
        data: Projection data dictionary

    Returns:
        str: Path to saved PNG file
    """
    print("📊 Creating chart image for Slack...")

    # Extract projection lines
    ideal = data['projections']['ideal']
    estimated = data['projections']['estimated']
    actual = data['projections']['actual']

    # Convert to separate lists for plotting
    ideal_dates = [datetime.strptime(p['date'], '%Y-%m-%d') for p in ideal]
    ideal_counts = [p['count'] for p in ideal]

    estimated_dates = [datetime.strptime(p['date'], '%Y-%m-%d') for p in estimated]
    estimated_counts = [p['count'] for p in estimated]

    actual_dates = [datetime.strptime(p['date'], '%Y-%m-%d') for p in actual]
    actual_counts = [p['count'] for p in actual]

    # Create figure
    fig = go.Figure()

    # Add Ideal line (solid black)
    fig.add_trace(go.Scatter(
        x=ideal_dates,
        y=ideal_counts,
        mode='lines',
        name='Ideal',
        line=dict(color='#000000', width=3)
    ))

    # Add Estimated line (orange, dashed)
    fig.add_trace(go.Scatter(
        x=estimated_dates,
        y=estimated_counts,
        mode='lines',
        name='Estimated',
        line=dict(color='#FFB366', width=4, dash='dash')
    ))

    # Add Actual line (green, solid with markers)
    fig.add_trace(go.Scatter(
        x=actual_dates,
        y=actual_counts,
        mode='lines+markers',
        name='Actual',
        line=dict(color='#27AE60', width=5),
        marker=dict(size=10, color='#27AE60', line=dict(color='white', width=2))
    ))

    # Add milestone markers
    milestones = data['key_dates']
    milestone_config = [
        {'key': 'code_freeze', 'label': 'Code Freeze', 'color': '#E74C3C'},
        {'key': 'submit', 'label': 'Submit', 'color': '#E67E22'},
        {'key': 'go_live', 'label': 'Go Live', 'color': '#27AE60'}
    ]

    for milestone in milestone_config:
        date_str = milestones[milestone['key']]
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')

        # Add vertical line
        fig.add_shape(
            type="line",
            x0=date_obj, x1=date_obj,
            y0=0, y1=1,
            yref="paper",
            line=dict(color=milestone['color'], width=2, dash='dot')
        )

        # Add label
        fig.add_annotation(
            x=date_obj,
            y=1,
            yref="paper",
            text=milestone['label'],
            showarrow=False,
            yshift=10,
            font=dict(size=12, color=milestone['color'], family='Arial Black')
        )

    # Layout configuration - optimized for Slack
    fig.update_layout(
        title={
            'text': '🔥 Spire 2.0.0 Bug Burndown',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#2C3E50', 'family': 'Arial Black'}
        },
        xaxis=dict(
            title='Date',
            gridcolor='#ECF0F1',
            showgrid=True,
            tickformat='%b %d',
            tickangle=-45
        ),
        yaxis=dict(
            title='Active Bugs',
            gridcolor='#ECF0F1',
            showgrid=True,
            rangemode='tozero'
        ),
        template='plotly_white',
        width=1200,  # Good size for Slack
        height=600,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(size=14)
        ),
        margin=dict(t=100, b=80, l=80, r=40)
    )

    # Save as PNG
    print(f"💾 Saving chart to {OUTPUT_IMAGE}...")
    fig.write_image(OUTPUT_IMAGE, format='png', scale=2)
    print(f"✅ Chart saved!")

    return OUTPUT_IMAGE


def generate_slack_message(data):
    """
    Generate Slack Block Kit message with key metrics.

    Args:
        data: Projection data dictionary

    Returns:
        dict: Slack Block Kit formatted message
    """
    print("📝 Generating Slack message...")

    current_bugs = data['current_active_bugs']
    required_rate = data['ideal_rate_per_day']
    estimated_rate = data.get('estimated_line_rate', data['historical_daily_rate'])
    estimated_rate_source = data.get('estimated_line_rate_source', 'historical average')
    velocity_gap = data['metrics']['velocity_gap']
    business_days_to_freeze = data.get('business_days_to_code_freeze', 0)
    go_live_date = data['key_dates']['go_live']

    # Determine status emoji
    if current_bugs <= 50:
        status_emoji = "🟢"
        status_text = "On track!"
    elif current_bugs <= 100:
        status_emoji = "🟡"
        status_text = "Needs attention"
    else:
        status_emoji = "🔴"
        status_text = "Critical - urgent action needed"

    # Create Slack Block Kit message
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔥 Spire 2.0.0 Bug Burndown Update",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Active Bugs:*\n{status_emoji} *{current_bugs}* bugs"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Days to Code Freeze:*\n⏰ *{business_days_to_freeze}* business days"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Required Rate:*\n📉 *{required_rate:.1f}* bugs/day"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Estimated Rate:*\n📊 *{estimated_rate:+.2f}* bugs/day\n_{estimated_rate_source}_"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Velocity Gap:*\n⚡ *{velocity_gap:.1f}x* improvement needed"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Go Live:*\n🎯 {go_live_date}"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"{status_emoji} *Status:* {status_text}"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📅 Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | 🔗 <https://taylorwestfall-12.github.io/Spire-2-0-burndown-/|View Full Dashboard>"
                }
            ]
        }
    ]

    message = {
        "blocks": blocks,
        "text": f"Spire 2.0.0 Burndown: {current_bugs} bugs remaining, {business_days_to_freeze} days to Code Freeze"
    }

    # Save to file
    print(f"💾 Saving message to {OUTPUT_MESSAGE}...")
    with open(OUTPUT_MESSAGE, 'w', encoding='utf-8') as f:
        json.dump(message, f, indent=2)
    print(f"✅ Message saved!")

    return message


def main():
    """Main execution."""
    print("🚀 Generating Slack Burndown Update")
    print("="*60)

    # Load data
    data = load_projections()

    # Create chart image
    chart_path = create_chart_image(data)

    # Generate Slack message
    message = generate_slack_message(data)

    print("\n" + "="*60)
    print("✅ SLACK CONTENT GENERATED!")
    print("="*60)
    print(f"\n📊 Chart: {chart_path}")
    print(f"📝 Message: {OUTPUT_MESSAGE}")
    print(f"\nPreview message:")
    print("-"*60)
    print(f"🔥 Spire 2.0.0 Bug Burndown Update")
    print(f"Active Bugs: {data['current_active_bugs']}")
    print(f"Days to Code Freeze: {data.get('business_days_to_code_freeze', 0)}")
    print(f"Required Rate: {data['ideal_rate_per_day']:.1f} bugs/day")
    print(f"Estimated Rate: {data.get('estimated_line_rate', data['historical_daily_rate']):+.2f} bugs/day")
    print("-"*60)
    print(f"\n💡 Next: Use post_to_slack.py to send to Slack channel")


if __name__ == "__main__":
    main()
