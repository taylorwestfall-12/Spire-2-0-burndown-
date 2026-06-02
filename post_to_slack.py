#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post Burndown Update to Slack

Posts the burndown chart and formatted message to Slack.
Requires: SLACK_BOT_TOKEN environment variable
"""

import os
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
CHART_IMAGE = "burndown_chart.png"
MESSAGE_FILE = "slack_message.json"


def post_to_slack(channel_or_user):
    """
    Post burndown update to Slack channel or user.

    Args:
        channel_or_user: Channel name (without #) or user ID
    """
    # Get token from environment
    token = os.getenv('SLACK_BOT_TOKEN')

    if not token:
        print("❌ Error: SLACK_BOT_TOKEN environment variable not set")
        print("\nTo set your token:")
        print("  Windows: set SLACK_BOT_TOKEN=xoxb-your-token-here")
        print("  Mac/Linux: export SLACK_BOT_TOKEN=xoxb-your-token-here")
        print("\nOr create a .env file with:")
        print("  SLACK_BOT_TOKEN=xoxb-your-token-here")
        sys.exit(1)

    # Initialize Slack client
    client = WebClient(token=token)

    print(f"📤 Posting to Slack: {channel_or_user}")

    try:
        # Load message blocks
        with open(MESSAGE_FILE, 'r', encoding='utf-8') as f:
            message_data = json.load(f)

        # Upload chart image
        print(f"📊 Uploading chart: {CHART_IMAGE}")
        upload_response = client.files_upload_v2(
            channel=channel_or_user,
            file=CHART_IMAGE,
            title="Spire 2.0.0 Bug Burndown Chart",
            initial_comment="📊 Latest burndown projection"
        )

        # Post message with blocks
        print(f"💬 Posting message...")
        message_response = client.chat_postMessage(
            channel=channel_or_user,
            blocks=message_data['blocks'],
            text=message_data['text']  # Fallback text for notifications
        )

        print(f"\n✅ Successfully posted to Slack!")
        print(f"   Channel: {message_response['channel']}")
        print(f"   Timestamp: {message_response['ts']}")

        # Get permalink
        permalink_response = client.chat_getPermalink(
            channel=message_response['channel'],
            message_ts=message_response['ts']
        )
        print(f"   Link: {permalink_response['permalink']}")

    except SlackApiError as e:
        print(f"\n❌ Slack API Error: {e.response['error']}")
        if e.response['error'] == 'not_authed':
            print("   → Check your SLACK_BOT_TOKEN is valid")
        elif e.response['error'] == 'channel_not_found':
            print(f"   → Channel '{channel_or_user}' not found")
            print("   → For DM: use your user ID (starts with U)")
            print("   → For channel: use channel ID (starts with C)")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e.filename}")
        print("   → Run generate_slack_burndown.py first")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


def main():
    """Main execution."""
    print("🚀 Slack Burndown Poster")
    print("="*60)

    # Check for target argument
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        # Default to DM to self (get user ID from token)
        target = input("Enter channel name or user ID (or press Enter for DM to yourself): ").strip()
        if not target:
            # Try to get authenticated user ID
            token = os.getenv('SLACK_BOT_TOKEN')
            if token:
                try:
                    from slack_sdk import WebClient
                    client = WebClient(token=token)
                    auth_response = client.auth_test()
                    target = auth_response['user_id']
                    print(f"📬 Sending DM to yourself ({target})")
                except:
                    print("❌ Could not determine user ID. Please provide a channel or user ID.")
                    sys.exit(1)

    # Post to Slack
    post_to_slack(target)


if __name__ == "__main__":
    main()
