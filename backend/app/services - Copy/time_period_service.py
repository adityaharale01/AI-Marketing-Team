import re
from typing import Any, Dict


# ============================================================
# TIME PERIOD SERVICE
# ============================================================

def detect_time_period(query: str) -> Dict[str, Any]:
    """
    Detect a relative time period from a business query.

    The current Business Analytics engine works with
    rolling periods based on the latest available sale.

    Supported examples:

        last 7 days
        last 14 days
        last 30 days
        last 60 days
        last 90 days
        past 7 days
        past 30 days
        previous 7 days
        previous 30 days
        recent 7 days
        recent 30 days

    If no period is specified, the existing default
    of 7 days is preserved.
    """

    if not query:
        return {
            "period_days": 7,
            "period_label": "last 7 days",
            "explicit": False,
        }

    q = query.lower().strip()

    # Normalize spaces
    q = re.sub(r"\s+", " ", q)

    # ========================================================
    # EXPLICIT NUMBER + DAYS
    # ========================================================

    patterns = [
        r"(?:last|past|previous|recent)\s+(\d+)\s+days?",
        r"(\d+)\s+days?",
    ]

    for pattern in patterns:

        match = re.search(pattern, q)

        if match:

            days = int(match.group(1))

            # Protect against invalid values
            if days <= 0:
                days = 7

            # Prevent unreasonable analytics windows
            days = min(days, 365)

            return {
                "period_days": days,
                "period_label": f"last {days} days",
                "explicit": True,
            }

    # ========================================================
    # COMMON NATURAL LANGUAGE PERIODS
    # ========================================================

    period_mapping = {

        # 1 day
        "today": 1,
        "today's": 1,
        "today sales": 1,
        "today revenue": 1,

        # 7 days
        "last week": 7,
        "past week": 7,
        "previous week": 7,
        "recent week": 7,
        "weekly": 7,

        # 14 days
        "last two weeks": 14,
        "past two weeks": 14,
        "previous two weeks": 14,
        "last 2 weeks": 14,
        "past 2 weeks": 14,

        # 30 days
        "last month": 30,
        "past month": 30,
        "previous month": 30,
        "recent month": 30,
        "monthly": 30,

        # 60 days
        "last two months": 60,
        "past two months": 60,
        "last 2 months": 60,
        "past 2 months": 60,

        # 90 days
        "last quarter": 90,
        "past quarter": 90,
        "previous quarter": 90,
        "quarterly": 90,
    }

    # Check longest phrases first
    for phrase in sorted(
        period_mapping.keys(),
        key=len,
        reverse=True,
    ):

        if phrase in q:

            days = period_mapping[phrase]

            return {
                "period_days": days,
                "period_label": f"last {days} days",
                "explicit": True,
            }

    # ========================================================
    # DEFAULT
    # ========================================================

    return {
        "period_days": 7,
        "period_label": "last 7 days",
        "explicit": False,
    }