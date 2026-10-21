"""Deterministic routing/formatting for aggregate business analytics queries.

PostgreSQL-derived analytics remain the source of truth; this module does not
call an LLM and does not calculate new metrics from product-level guesses.
"""
import re
from typing import Any, Dict, Optional


def is_overall_growth_query(query: str) -> bool:
    q = re.sub(r"[^a-z0-9%\s]", " ", (query or "").lower())
    q = re.sub(r"\s+", " ", q).strip()

    # Do not steal clearly product-specific questions.
    product_specific = any(x in q for x in (
        "which product", "which products", "this product", "product ",
        "cheese sandwich", "red velvet", "butter cookies", "garlic bread",
        "brown bread", "fruit tart", "muffin", "chocolate muffin",
    ))
    if product_specific:
        return False

    aggregate_metric = any(x in q for x in (
        "revenue growth", "quantity growth", "growth over", "overall growth",
        "overall performance", "overall sales", "sales growth", "revenue and quantity",
        "recent and previous totals", "recent vs previous", "compare recent",
        "compare the last", "compare last", "compare sales", "total revenue",
        "total quantity", "units sold and revenue", "sales and revenue",
    ))
    growth_word = any(x in q for x in ("growth", "grew", "increased", "decreased", "change", "compare"))
    asks_totals = any(x in q for x in ("recent", "previous", "totals", "last 30 days", "last 7 days", "last 14 days"))
    asks_both = "revenue" in q and any(x in q for x in ("quantity", "units", "unit"))
    return aggregate_metric or (asks_both and growth_word) or (asks_totals and growth_word and "sales" in q)


def _money(value: Any) -> str:
    try:
        return f"₹{float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "Unavailable"


def _number(value: Any) -> str:
    try:
        n = float(value or 0)
        return f"{int(n):,}" if n.is_integer() else f"{n:,.2f}"
    except (TypeError, ValueError):
        return "Unavailable"


def _growth(value: Optional[Any]) -> str:
    if value is None:
        return "Not calculable (no previous-period baseline)"
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return "Unavailable"


def format_overall_growth_answer(analytics: Dict[str, Any], period_label: str) -> str:
    overall = analytics.get("overall") or {}
    # Compatibility with older analytics payloads that may expose top-level totals.
    recent_quantity = overall.get("recent_quantity", analytics.get("recent_quantity"))
    previous_quantity = overall.get("previous_quantity", analytics.get("previous_quantity"))
    recent_revenue = overall.get("recent_revenue", analytics.get("recent_revenue"))
    previous_revenue = overall.get("previous_revenue", analytics.get("previous_revenue"))
    quantity_growth = overall.get("quantity_growth_percent", analytics.get("quantity_growth_percent"))
    revenue_growth = overall.get("revenue_growth_percent", analytics.get("revenue_growth_percent"))

    if analytics.get("message") == "No sales data available." or not overall and all(
        analytics.get(k) is None for k in ("recent_quantity", "previous_quantity", "recent_revenue", "previous_revenue")
    ):
        return "I cannot calculate overall revenue or quantity growth because this business has no sales data in the analytics result. Add or verify sales records for this business, then try again."

    return (
        f"Overall performance for {analytics.get('business_name', 'this business')} ({period_label} vs the previous {overall.get('period_days', analytics.get('period_days', 'same-length'))}):\n\n"
        f"Revenue\n"
        f"• Previous total: {_money(previous_revenue)}\n"
        f"• Recent total: {_money(recent_revenue)}\n"
        f"• Revenue growth: {_growth(revenue_growth)}\n\n"
        f"Quantity sold\n"
        f"• Previous total: {_number(previous_quantity)} units\n"
        f"• Recent total: {_number(recent_quantity)} units\n"
        f"• Quantity growth: {_growth(quantity_growth)}\n\n"
        "Growth is calculated as (recent total − previous total) / previous total × 100. "
        "A percentage is not calculated when the previous-period total is zero or unavailable."
    )
