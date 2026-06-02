#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QA Status Utilities

Helper functions for working with the ClickUp "QA Status (sp)" custom field.
"""

# QA Status field ID in ClickUp
QA_STATUS_FIELD_ID = "67ea8f39-eef6-4786-bab9-61586a1a5814"

# QA Status value mapping
QA_STATUS_NAMES = {
    0: "Ready for Test",
    1: "QA Review",
    2: "Need Info/Testing/Confirmation",
    3: "Triage",
    4: "Open",
    5: "Reopened",
    6: "Blocked",
    7: "Fix in Progress",
    8: "Pending Build",
    9: "Not Reproducible",
    10: "Duplicated",
    11: "Not a Bug",
    12: "Won't Fix",
    13: "QA Pass",
    14: "Logs"
}

# QA Status values that should always be excluded (resolved/invalid bugs)
# These represent bugs that are not actually active work, even if main Status isn't "Closed"
EXCLUDED_QA_STATUSES = [10, 11, 12, 13]  # Duplicated, Not a Bug, Won't Fix, QA Pass


def get_qa_status_value(bug):
    """
    Extract QA Status value from a bug's custom fields.

    Args:
        bug: Bug dictionary (either from raw ClickUp data or parsed data)

    Returns:
        int: QA Status value (0-14), or None if not set
    """
    # Check if already parsed (has qa_status field directly)
    if 'qa_status' in bug:
        return bug.get('qa_status')

    # Otherwise extract from custom_fields (raw ClickUp format)
    custom_fields = bug.get('custom_fields', [])
    if isinstance(custom_fields, list):
        for field in custom_fields:
            if field.get('id') == QA_STATUS_FIELD_ID:
                return field.get('value')

    return None


def get_qa_status_name(qa_status_value):
    """
    Get the name of a QA Status value.

    Args:
        qa_status_value: QA Status value (0-14)

    Returns:
        str: QA Status name, or "Unknown" if not found
    """
    if qa_status_value is None:
        return "Not Set"
    return QA_STATUS_NAMES.get(qa_status_value, f"Unknown ({qa_status_value})")


def is_active_qa_status(qa_status_value):
    """
    Check if a QA Status value represents active work.

    All QA Status values are considered active EXCEPT the excluded ones
    (Won't Fix, Not a Bug, Duplicated, QA Pass).

    Args:
        qa_status_value: QA Status value

    Returns:
        bool: True if this QA Status should be counted as active
    """
    # If QA Status is None (not set), consider it active
    if qa_status_value is None:
        return True

    # If it's in the excluded list, it's not active
    return qa_status_value not in EXCLUDED_QA_STATUSES


def should_exclude_qa_status(qa_status_value):
    """
    Check if a QA Status value should always be excluded (resolved/invalid).

    Args:
        qa_status_value: QA Status value

    Returns:
        bool: True if this QA Status should always be excluded
    """
    return qa_status_value in EXCLUDED_QA_STATUSES


def is_clickup_visible_bug(bug):
    """
    Check if a bug should be counted as active for the burndown.

    Criteria:
    - Must have milestone = "2.0.0 Global"
    - Main Status must not be Closed/Won't Fix
    - QA Status must not be Won't Fix/Not a Bug/Duplicated/QA Pass

    Note: All bugs in qa, in progress, code review, to-do, etc. are counted as active.
    The QA Status custom field is for QA workflow tracking - we only exclude truly
    invalid/resolved QA Status values.

    Args:
        bug: Bug dictionary

    Returns:
        bool: True if bug should be counted as active
    """
    # Check milestone
    milestone = bug.get('milestone_simplified')
    if milestone != '2.0.0 Global':
        return False

    # Check main status
    status = bug.get('status', '')
    excluded_statuses = ['Closed', 'closed', "won't fix", "Won't Fix", "WON'T FIX"]
    if status in excluded_statuses:
        return False

    # Check QA Status - only exclude truly invalid/resolved states
    qa_status = get_qa_status_value(bug)

    # Exclude bugs marked as Won't Fix, Not a Bug, Duplicated, or QA Pass in QA Status field
    return is_active_qa_status(qa_status)
