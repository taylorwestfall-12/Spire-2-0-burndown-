#!/usr/bin/env python3
"""
ClickUp Batch Bug Fetcher
Fetches all bugs from ClickUp using REST API and saves to local JSON file.
Avoids MCP tools - uses direct API calls with pagination for efficiency.
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ClickUp API Configuration
API_KEY = os.getenv('CLICKUP_API_KEY')
LIST_ID = os.getenv('CLICKUP_LIST_ID', '901207871711')
BASE_URL = 'https://api.clickup.com/api/v2'

# Output file configuration
OUTPUT_FILE = 'spire_bugs_complete.json'
CHECKPOINT_FILE = 'fetch_checkpoint.json'

# API request configuration
HEADERS = {
    'Authorization': API_KEY,
    'Content-Type': 'application/json'
}

# Rate limiting (ClickUp has rate limits, be respectful)
RATE_LIMIT_DELAY = 0.5  # seconds between requests


class ClickUpBatchFetcher:
    """Fetches all tasks from a ClickUp list with progress tracking and resumability."""

    def __init__(self, api_key: str, list_id: str):
        self.api_key = api_key
        self.list_id = list_id
        self.headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
        self.base_url = BASE_URL
        self.all_bugs = []
        self.total_fetched = 0

    def fetch_all_tasks(self, include_closed: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch all tasks from the ClickUp list using pagination.

        Args:
            include_closed: Whether to include closed/completed tasks

        Returns:
            List of all tasks with full details
        """
        print(f"\n{'='*60}")
        print(f"Starting batch fetch from ClickUp List: {self.list_id}")
        print(f"Include closed tasks: {include_closed}")
        print(f"{'='*60}\n")

        page = 0
        has_more = True

        while has_more:
            print(f"Fetching page {page}...")

            # Build request URL with parameters
            url = f"{self.base_url}/list/{self.list_id}/task"
            params = {
                'page': page,
                'include_closed': str(include_closed).lower(),
                'subtasks': 'false',  # We only want top-level bugs
            }

            try:
                # Make API request
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                # Parse response
                data = response.json()
                tasks = data.get('tasks', [])

                if not tasks:
                    print(f"  No more tasks found on page {page}")
                    has_more = False
                else:
                    # Add tasks to our collection
                    self.all_bugs.extend(tasks)
                    self.total_fetched += len(tasks)

                    print(f"  [OK] Fetched {len(tasks)} tasks (Total: {self.total_fetched})")

                    # Save checkpoint after each page
                    self._save_checkpoint(page, self.total_fetched)

                    # Check if there are more pages
                    # ClickUp returns empty list when no more tasks
                    page += 1

                    # Respect rate limits
                    time.sleep(RATE_LIMIT_DELAY)

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"  List not found. Check LIST_ID: {self.list_id}")
                    break
                elif e.response.status_code == 401:
                    print(f"  Authentication failed. Check your API key.")
                    break
                elif e.response.status_code == 429:
                    print(f"  Rate limited. Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                else:
                    print(f"  HTTP Error: {e}")
                    print(f"  Response: {e.response.text}")
                    break

            except Exception as e:
                print(f"  Error fetching page {page}: {e}")
                break

        print(f"\n{'='*60}")
        print(f"Batch fetch complete!")
        print(f"Total bugs fetched: {self.total_fetched}")
        print(f"{'='*60}\n")

        return self.all_bugs

    def _save_checkpoint(self, page: int, total: int):
        """Save progress checkpoint for resumability."""
        checkpoint = {
            'last_page': page,
            'total_fetched': total,
            'timestamp': datetime.now().isoformat(),
            'list_id': self.list_id
        }

        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(checkpoint, f, indent=2)

    def save_to_file(self, filename: str, pretty: bool = True):
        """
        Save all fetched bugs to a JSON file.

        Args:
            filename: Output filename
            pretty: Whether to pretty-print JSON (indent=2)
        """
        print(f"Saving {len(self.all_bugs)} bugs to {filename}...")

        # Prepare output data with metadata
        output = {
            'metadata': {
                'total_bugs': len(self.all_bugs),
                'list_id': self.list_id,
                'fetched_at': datetime.now().isoformat(),
                'source': 'ClickUp REST API'
            },
            'bugs': self.all_bugs
        }

        with open(filename, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(output, f, indent=2, ensure_ascii=False)
            else:
                json.dump(output, f, ensure_ascii=False)

        print(f"[OK] Saved successfully to {filename}")
        print(f"  File size: {os.path.getsize(filename) / 1024:.2f} KB")

    def print_summary(self):
        """Print a summary of fetched data."""
        if not self.all_bugs:
            print("No bugs fetched yet.")
            return

        print(f"\n{'='*60}")
        print("FETCH SUMMARY")
        print(f"{'='*60}")
        print(f"Total bugs: {len(self.all_bugs)}")

        # Status breakdown
        statuses = {}
        for bug in self.all_bugs:
            status_name = bug.get('status', {}).get('status', 'Unknown')
            statuses[status_name] = statuses.get(status_name, 0) + 1

        print(f"\nStatus breakdown:")
        for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True):
            print(f"  {status}: {count}")

        # Check for required fields
        print(f"\nData quality check:")
        has_date_created = sum(1 for b in self.all_bugs if b.get('date_created'))
        has_date_closed = sum(1 for b in self.all_bugs if b.get('date_closed'))
        has_custom_fields = sum(1 for b in self.all_bugs if b.get('custom_fields'))

        print(f"  [OK] date_created: {has_date_created}/{len(self.all_bugs)}")
        print(f"  [OK] date_closed: {has_date_closed}/{len(self.all_bugs)}")
        print(f"  [OK] custom_fields: {has_custom_fields}/{len(self.all_bugs)}")

        # Sample bug IDs
        print(f"\nSample bug IDs (first 5):")
        for bug in self.all_bugs[:5]:
            bug_id = bug.get('id')
            name = bug.get('name', 'No name')[:50]
            print(f"  {bug_id}: {name}")

        print(f"{'='*60}\n")


def main():
    """Main execution function."""
    # Validate configuration
    if not API_KEY:
        print("ERROR: CLICKUP_API_KEY not found in environment")
        print("Please create a .env file with your ClickUp API key:")
        print("  CLICKUP_API_KEY=your_api_key_here")
        print("  CLICKUP_LIST_ID=901207871711")
        return

    if not LIST_ID:
        print("ERROR: CLICKUP_LIST_ID not found in environment")
        return

    # Create fetcher
    fetcher = ClickUpBatchFetcher(API_KEY, LIST_ID)

    # Fetch all tasks (including closed ones for burndown analysis)
    bugs = fetcher.fetch_all_tasks(include_closed=True)

    if bugs:
        # Save to file
        fetcher.save_to_file(OUTPUT_FILE, pretty=True)

        # Print summary
        fetcher.print_summary()

        print(f"\n[SUCCESS!]")
        print(f"All bug data saved to: {OUTPUT_FILE}")
        print(f"Checkpoint saved to: {CHECKPOINT_FILE}")
        print(f"\nNext steps:")
        print(f"  1. Review the data in {OUTPUT_FILE}")
        print(f"  2. Run analysis scripts to process burndown metrics")
        print(f"  3. Generate dashboard visualizations")
    else:
        print("\n[WARNING] No bugs were fetched. Check your configuration and try again.")


if __name__ == '__main__':
    main()
