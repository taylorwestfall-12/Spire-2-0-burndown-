#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recalculate Burndown Projections with Complete Actual Data

Uses the complete actual data from May 11 - June 2 (no gaps).
"""

import json
import sys
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

COMPLETE_ACTUALS_FILE = "complete_actuals_may11_jun02.json"
PROJECTIONS_FILE = "burndown_projections.json"


def main():
    """Update projections with complete actual data."""
    print("🔄 Updating burndown projections with complete actual data...")

    # Load complete actuals
    with open(COMPLETE_ACTUALS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    actuals = data['actuals']
    print(f"   Loaded {len(actuals)} actual data points")
    print(f"   Range: {actuals[0]['date']} to {actuals[-1]['date']}")
    print(f"   Start: {actuals[0]['count']} bugs")
    print(f"   End: {actuals[-1]['count']} bugs")

    # Load current projections
    with open(PROJECTIONS_FILE, 'r', encoding='utf-8') as f:
        projections = json.load(f)

    # Update actual line
    projections['projections']['actual'] = actuals

    # Update current_active_bugs
    projections['current_active_bugs'] = actuals[-1]['count']

    # Update today's date
    projections['key_dates']['today'] = actuals[-1]['date']

    # Save
    with open(PROJECTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(projections, f, indent=2)

    print(f"\n✅ Updated {PROJECTIONS_FILE}")
    print(f"   Current bugs: {actuals[-1]['count']}")
    print(f"   Today: {actuals[-1]['date']}")


if __name__ == "__main__":
    main()
