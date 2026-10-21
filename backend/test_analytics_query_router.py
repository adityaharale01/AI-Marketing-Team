import unittest
from app.services.analytics_query_router import (
    is_overall_growth_query,
    format_overall_growth_answer,
)


class AnalyticsQueryRouterTests(unittest.TestCase):
    def test_aggregate_growth_queries_route_to_overall(self):
        queries = [
            "What is my revenue growth and quantity growth over the last 30 days? Show the recent and previous totals.",
            "Compare recent and previous revenue and units sold",
            "What is my overall sales growth?",
            "Show overall performance for last 7 days",
        ]
        for query in queries:
            with self.subTest(query=query):
                self.assertTrue(is_overall_growth_query(query))

    def test_product_queries_do_not_route_to_overall(self):
        queries = [
            "Which products are showing increasing sales?",
            "How is Red Velvet Cake performing over the last 30 days?",
            "Which product has the highest revenue?",
        ]
        for query in queries:
            with self.subTest(query=query):
                self.assertFalse(is_overall_growth_query(query))

    def test_format_uses_verified_totals_and_growth(self):
        analytics = {
            "business_name": "Sweet Crust",
            "period_days": 30,
            "overall": {
                "period_days": 30,
                "recent_quantity": 2991,
                "previous_quantity": 3085,
                "recent_revenue": 832830,
                "previous_revenue": 917000,
                "quantity_growth_percent": -3.05,
                "revenue_growth_percent": -9.18,
            },
        }
        answer = format_overall_growth_answer(analytics, "last 30 days")
        self.assertIn("₹917,000.00", answer)
        self.assertIn("₹832,830.00", answer)
        self.assertIn("3,085 units", answer)
        self.assertIn("2,991 units", answer)
        self.assertIn("-9.18%", answer)
        self.assertIn("-3.05%", answer)

    def test_zero_previous_baseline_is_not_divided_by_zero(self):
        analytics = {
            "business_name": "Test Bakery",
            "period_days": 30,
            "overall": {
                "period_days": 30,
                "recent_quantity": 5,
                "previous_quantity": 0,
                "recent_revenue": 500,
                "previous_revenue": 0,
                "quantity_growth_percent": None,
                "revenue_growth_percent": None,
            },
        }
        answer = format_overall_growth_answer(analytics, "last 30 days")
        self.assertIn("Not calculable (no previous-period baseline)", answer)


if __name__ == "__main__":
    unittest.main()
