"""Regression tests for the inventory-safety promotion route.

Run from the backend root with: pytest tests/test_not_promote_routing.py -q
"""
import asyncio

from app.services import business_agent


BASE_ANALYTICS = {
    "business_name": "Fresh Bake House",
    "business_category": "Bakery",
    "latest_sale_date": "2026-10-03T19:50:39+05:30",
    "overall": {"recent_revenue": 1000, "previous_revenue": 1200,
                "recent_quantity": 20, "previous_quantity": 25},
    "products": [
        {"product_name": "Chocolate Cake", "stock": 0,
         "recent_quantity": 3, "previous_quantity": 8,
         "recent_revenue": 1200, "growth_percent": -62.5},
        {"product_name": "Red Velvet Cake", "stock": 12,
         "recent_quantity": 5, "previous_quantity": 4,
         "recent_revenue": 900, "growth_percent": 25.0},
    ],
}


def run_query(monkeypatch, query, products=None):
    analytics = dict(BASE_ANALYTICS)
    analytics["products"] = products if products is not None else BASE_ANALYTICS["products"]
    monkeypatch.setattr(business_agent, "get_business_analytics", lambda **kwargs: analytics)
    monkeypatch.setattr(business_agent, "detect_time_period", lambda q: {
        "period_days": 7, "period_label": "last 7 days", "explicit": False
    })
    return asyncio.run(business_agent.ask_business_agent(None, 2, query))


def test_not_promote_returns_out_of_stock_not_general_opportunities(monkeypatch):
    result = run_query(monkeypatch, "Which product should I not promote?")
    answer = result["answer"]
    assert "Chocolate Cake" in answer
    assert "stock 0" in answer
    assert "Red Velvet Cake" not in answer
    assert "Promotion Opportunities" not in answer


def test_avoid_advertising_variant_routes_to_stock_safety(monkeypatch):
    result = run_query(monkeypatch, "Which products should I avoid advertising?")
    assert "Chocolate Cake" in result["answer"]
    assert "stock 0" in result["answer"]
    assert "Promotion Opportunities" not in result["answer"]


def test_no_zero_stock_does_not_invent_exclusions(monkeypatch):
    products = [dict(BASE_ANALYTICS["products"][1])]
    result = run_query(monkeypatch, "Which product should I not promote?", products)
    assert "No products are currently out of stock" in result["answer"]
    assert "Red Velvet Cake" not in result["answer"]


def test_out_of_stock_route_does_not_depend_on_sales_growth(monkeypatch):
    products = [
        {"product_name": "Unavailable Item", "stock": 0,
         "recent_quantity": 0, "previous_quantity": 0,
         "recent_revenue": 0, "growth_percent": None},
    ]
    result = run_query(monkeypatch, "What should I not promote?", products)
    assert "Unavailable Item" in result["answer"]
    assert "stock 0" in result["answer"]
