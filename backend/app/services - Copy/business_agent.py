# app/services/business_agent.py

from typing import Any, Dict, List

from sqlalchemy.orm import Session


from app.services.business_analytics_service import (
    get_business_analytics,
)

from app.services.analytics_query_router import (
    is_overall_growth_query,
    format_overall_growth_answer,
)


from app.services.time_period_service import (
    detect_time_period,
)


from app.services.rag_service import (
    search_business_context,
    build_context,
)


from app.services.ollama_service import (
    generate_response,
)


from app.services.query_intent_service import (
    classify_query,
)


from app.services.business_recommendation_service import (
    get_product_recommendation,
    recommend_for_declining_products,
    recommend_for_increasing_products,
    recommend_for_out_of_stock_products,
    recommend_for_low_stock_products,
    generate_business_recommendations,
)


from app.services.promotion_service import (
    get_promotion_opportunities,
    get_declining_promotion_opportunities,
    get_growing_promotion_opportunities,
    generate_promotion_summary,
)


# ============================================================
# BUSINESS AGENT
# ============================================================


async def ask_business_agent(
    db: Session,
    business_id: int,
    query: str,
) -> Dict[str, Any]:

    # ========================================================
    # 1. DETECT TIME PERIOD
    # ========================================================

    time_period = detect_time_period(
        query
    )

    period_days = time_period.get(
        "period_days",
        7,
    )

    period_label = time_period.get(
        "period_label",
        "last 7 days",
    )

    period_explicit = time_period.get(
        "explicit",
        False,
    )


    # ========================================================
    # 2. GET VERIFIED BUSINESS ANALYTICS
    # ========================================================

    analytics = get_business_analytics(
        db=db,
        business_id=business_id,
        period_days=period_days,
    )


    if not analytics:

        return {
            "business_id": business_id,
            "query": query,
            "answer": "Unable to find business analytics.",
            "intents": [],
            "time_period": {
                "period_days": period_days,
                "period_label": period_label,
                "explicit": period_explicit,
            },
            "analytics": {},
            "rag_context": "",
        }


    business_name = analytics.get(
        "business_name",
        "Business",
    )


    products = analytics.get(
        "products",
        [],
    )

    # Deterministic answers for common business questions. These use only
    # PostgreSQL analytics and existing promotion rules; the LLM is not asked
    # to invent numeric business facts.
    q = " ".join((query or "").lower().replace("’", "'").replace("-", " ").split())
    overall = analytics.get("overall", {}) or {}

    def money(value):
        return f"₹{float(value or 0):,.2f}"

    def pct(value):
        return "unavailable (no previous-period baseline)" if value is None else f"{float(value):+.2f}%"

    def product_lines(items, metric="recent_quantity", label="units sold"):
        if not items:
            return "No matching products were found in the selected business data."
        return "\n".join(
            f"{i}. {p.get('product_name', 'Unknown product')} — {p.get(metric, 0)} {label}; "
            f"revenue {money(p.get('recent_revenue', 0))}; stock {int(p.get('stock', 0) or 0)}"
            for i, p in enumerate(items, 1)
        )

    answer = None

    # Safety-first promotion routing: a question asking what NOT to promote
    # is an inventory decision, not a request for the general promotion list.
    # Evaluate it before any broad promotion/recovery opportunity routing.
    asks_what_not_to_promote = (
        any(phrase in q for phrase in (
            "not promote", "shouldn't promote", "should not promote",
            "avoid promoting", "not advertise", "should not advertise",
            "shouldn't advertise", "avoid advertising",
        ))
        or ("promote" in q and any(word in q for word in ("avoid", "shouldn't", "should not", "not recommend")))
    )
    if asks_what_not_to_promote:
        unavailable = sorted(
            [p for p in products if int(p.get("stock", 0) or 0) <= 0],
            key=lambda p: str(p.get("product_name", "" )).lower(),
        )
        if unavailable:
            names = "\n".join(
                f"- {p.get('product_name', 'Unknown product')} — stock 0"
                for p in unavailable
            )
            answer = (
                "Do not promote these products until inventory is replenished "
                f"(current stock from the Product table):\n{names}\n"
                "This recommendation is based on stock availability. Sales decline alone "
                "does not prove a product should never be promoted."
            )
        else:
            answer = (
                "No products are currently out of stock, so the available inventory data "
                "does not identify a product that must be excluded from promotion for zero stock. "
                "Review product availability, margins, campaign costs, and campaign results "
                "before deciding whether to exclude a product for other reasons."
            )

    # Business identity / scope
    if answer is not None:
        pass  # Safety-first routing above has already answered this question.
    elif ("selected business" in q or "only results for my business" in q or "only this business" in q):
        answer = f"All figures in this response are filtered to business_id={business_id} ({business_name}); product inventory is read from that business's Product records and sales are filtered by Sale.business_id."
    elif any(x in q for x in ("business name", "business category", "what is my business")):
        answer = f"Business: {business_name}. Category: {analytics.get('business_category') or 'unavailable in the business profile data'}. Business ID: {business_id}."
    elif any(x in q for x in ("how many products", "number of products", "product count")):
        answer = f"{business_name} has {len(products)} products in the selected business's product table."
    elif "profit" in q:
        answer = "Profit cannot be calculated from the available fields because product cost/COGS and operating expenses are not available. Revenue is not the same as profit."
    elif "why is a product missing" in q or "missing from this report" in q:
        answer = (f"This report is scoped to business_id={business_id} ({business_name}) and {period_label}. A product can be absent because it belongs to another business, has no Sale rows in the selected period, has zero units in that period, or is excluded by the report's ranking/filter. Current stock comes from the Product table; sales and growth come from Sale records. Check the product's business_id, Sale rows/date range, product_id linkage, and whether the report filters to products with sales. Aggregate data alone cannot identify the exact cause for a specific missing product unless its records are checked.")
    elif "sales data is missing" in q or "what is unavailable" in q:
        answer = (f"Data available for business_id={business_id} ({business_name}): product names/categories and current stock from Product records; recorded units/revenue and period comparisons from Sale records. The comparison anchor is the latest recorded sale ({analytics.get('latest_sale_date')}). Unavailable unless separately stored: profit (COGS/expenses), margins, campaign spend and attribution, customer preferences, and product co-purchase/basket evidence. Growth is unavailable when the previous-period baseline is zero. If sales records are absent, sales totals, revenue, growth, top sellers, and sales-based recommendations are unavailable; current inventory may still be available from Product records.")
    elif any(x in q for x in ("what data was used", "data was used")):
        answer = (f"This answer uses business_id={business_id} only, product stock from the Product table, and Sale records for that business. "
                  f"The analytics comparison is anchored to the latest recorded sale ({analytics.get('latest_sale_date')}). "
                  "Missing baselines are reported as unavailable, not 0% growth. Profit is unavailable without cost/expense fields; customer preferences and product-pair purchase data are not inferred from aggregate sales.")
    elif "currently in stock" in q or ("each product" in q and "stock" in q):
        answer = "Current stock from the Product table (not units sold):\n" + ("\n".join(f"- {p.get('product_name', 'Unknown product')}: {int(p.get('stock', 0) or 0)} units" for p in sorted(products, key=lambda p: p.get('product_name', ''))) or "No products found.")
    # Overall rolling period metrics
    elif "average daily revenue" in q:
        answer = f"Average daily revenue for {period_label}: {money(analytics.get('average_daily_revenue'))}. Calculation: recent-period revenue ÷ {period_days} calendar days. Period is anchored to latest recorded sale {analytics.get('latest_sale_date')}."
    elif any(x in q for x in ("highest sales", "sales highest", "highest-selling date", "which date")) and "date" in q:
        peak = analytics.get("highest_sales_date")
        answer = f"Highest recorded sales date across available history: {peak['date']} with revenue {money(peak['revenue'])}." if peak else "Unavailable: there are no sales records for this business."
    elif "this month" in q or "previous month" in q or "last month" in q:
        m = analytics.get("calendar_month_comparison") or {}
        answer = (f"Calendar-month comparison (anchored to latest recorded sale): current month revenue {money(m.get('recent_revenue'))}, previous month revenue {money(m.get('previous_revenue'))}; "
                  f"revenue change {money(m.get('revenue_change'))}, growth {pct(m.get('revenue_growth_percent'))}. "
                  f"Units: current {m.get('recent_quantity', 0)}, previous {m.get('previous_quantity', 0)}, change {m.get('quantity_change', 0)}; quantity growth {pct(m.get('quantity_growth_percent'))}. "
                  "Growth formula = (recent − previous) ÷ previous × 100; if previous is zero, growth is unavailable.")
    elif "revenue change" in q or ("change in rupees" in q and "revenue" in q):
        recent = float(overall.get("recent_revenue", 0) or 0)
        previous = float(overall.get("previous_revenue", 0) or 0)
        answer = f"Revenue change for {period_label}: recent revenue {money(recent)}; previous revenue {money(previous)}; change {money(recent - previous)}; growth {pct(overall.get('revenue_growth_percent'))}."
    elif "revenue growth" in q or "quantity growth" in q or "performing better" in q or "performing worse" in q or "overall business performance" in q:
        rg, qg = overall.get("revenue_growth_percent"), overall.get("quantity_growth_percent")
        direction = "better" if rg is not None and qg is not None and rg > 0 and qg > 0 else "worse" if rg is not None and qg is not None and rg < 0 and qg < 0 else "mixed or inconclusive"
        answer = (f"Business performance — {period_label} vs preceding {period_days} days (latest sale anchor {analytics.get('latest_sale_date')}):\n"
                  f"Revenue: recent {money(overall.get('recent_revenue'))}; previous {money(overall.get('previous_revenue'))}; change {money(float(overall.get('recent_revenue', 0) or 0)-float(overall.get('previous_revenue', 0) or 0))}; growth {pct(rg)}.\n"
                  f"Quantity: recent {overall.get('recent_quantity', 0)} units; previous {overall.get('previous_quantity', 0)} units; change {int(overall.get('recent_quantity', 0) or 0)-int(overall.get('previous_quantity', 0) or 0)} units; growth {pct(qg)}.\n"
                  "Formula for each growth rate: (recent total − previous total) ÷ previous total × 100. "
                  f"Overall direction: {direction}. A growth rate is unavailable when the previous total is zero.")
    elif "total revenue" in q or ("revenue" in q and "last 7 days" in q):
        answer = f"Total revenue for {period_label}: {money(overall.get('recent_revenue'))}. Units sold: {overall.get('recent_quantity', 0)}."
    elif "how many units" in q or "units did" in q or "total quantity" in q:
        answer = f"Units sold for {period_label}: {overall.get('recent_quantity', 0)}. Previous comparable period: {overall.get('previous_quantity', 0)} units."
    # Inventory
    elif "out of stock" in q or "stock is zero" in q or "stock zero" in q:
        items = [p for p in products if int(p.get("stock", 0) or 0) == 0]
        answer = "Products currently out of stock (current Product table):\n" + ("\n".join(f"- {p['product_name']} — 0 units" for p in items) if items else "None.")
        if "promot" in q: answer += "\nDo not promote these products until stock is replenished."
    elif "low inventory" in q or "low stock" in q:
        items = sorted([p for p in products if 0 < int(p.get("stock", 0) or 0) <= 5], key=lambda p: int(p.get("stock", 0) or 0))
        answer = "Low inventory threshold used: 1–5 units.\n" + ("\n".join(f"- {p['product_name']}: {p['stock']} units" for p in items) if items else "No products have 1–5 units in stock.")
    elif "best-selling" in q and ("restock" in q or "restocking" in q):
        items = sorted([p for p in products if 0 < int(p.get("stock", 0) or 0) <= 5], key=lambda p: int(p.get("recent_quantity", 0) or 0), reverse=True)
        answer = ("Best-selling products that may need restocking (low-stock threshold: 1–5 units):\n" + product_lines(items[:5])) if items else "There are currently no products with low stock."
    elif "high stock" in q and "declining" in q:
        items = [p for p in products if p.get('growth_percent') is not None and float(p['growth_percent']) < -10 and int(p.get('stock', 0) or 0) > 30]
        answer = "Products with stock above 30 units and quantity growth below −10%: (thresholds are explicit screening rules)\n" + product_lines(items)
    # Product performance
    elif "no sales" in q:
        items = [p for p in products if int(p.get('recent_quantity', 0) or 0) == 0]
        answer = f"Products with zero recorded units in {period_label}:\n" + ("\n".join(f"- {p['product_name']} (stock {p.get('stock', 0)})" for p in items) if items else "Every listed product has at least one recorded unit sold in this period.")
    elif "new seller" in q or "no previous sales" in q or "no previous-period baseline" in q:
        items = [p for p in products if int(p.get('previous_quantity', 0) or 0) == 0 and int(p.get('recent_quantity', 0) or 0) > 0]
        answer = "Products with recent sales but zero previous-period units (growth % is undefined):\n" + product_lines(items)
    elif "biggest revenue decline" in q or "revenue decline" in q:
        eligible = [p for p in products if p.get("revenue_growth_percent") is not None]
        items = sorted(eligible, key=lambda p: float(p.get("recent_revenue", 0) or 0) - float(p.get("previous_revenue", 0) or 0))
        if items:
            p = items[0]
            answer = f"Largest product revenue decline: {p['product_name']} — change {money(float(p.get('recent_revenue', 0) or 0)-float(p.get('previous_revenue', 0) or 0))}; previous revenue {money(p.get('previous_revenue'))}, recent revenue {money(p.get('recent_revenue'))}, revenue growth {pct(p.get('revenue_growth_percent'))}."
        else:
            answer = "Unavailable: no product has a positive previous-period revenue baseline, so revenue decline cannot be calculated."
    elif "largest increase in units" in q or "largest increase" in q:
        eligible = [p for p in products if p.get('growth_percent') is not None]
        items = sorted(eligible, key=lambda p: int(p.get('recent_quantity', 0) or 0)-int(p.get('previous_quantity', 0) or 0), reverse=True)
        if items:
            p=items[0]; answer=f"Largest increase in units: {p['product_name']} — {int(p.get('recent_quantity',0))-int(p.get('previous_quantity',0)):+d} units ({p.get('previous_quantity',0)} previous → {p.get('recent_quantity',0)} recent)."
        else: answer="Unavailable: no products have a valid previous-period quantity baseline."
    elif "compare" in q and " and " in q and any(p.get('product_name','').lower() in q for p in products):
        matches = [p for p in products if p.get('product_name','').lower() in q]
        if len(matches) >= 2:
            answer = "Product comparison for " + period_label + ":\n" + "\n".join(f"- {p['product_name']}: {p.get('recent_quantity',0)} units (previous {p.get('previous_quantity',0)}), revenue {money(p.get('recent_revenue'))}, quantity growth {pct(p.get('growth_percent'))}, stock {p.get('stock',0)}" for p in matches[:2])
    elif any(p.get('product_name','').lower() in q for p in products):
        matches = [p for p in products if p.get('product_name','').lower() in q]
        if matches:
            p=matches[0]
            answer = f"{p['product_name']} — {period_label}: {p.get('recent_quantity',0)} units sold (previous period {p.get('previous_quantity',0)}), recent revenue {money(p.get('recent_revenue'))}, quantity growth {pct(p.get('growth_percent'))}, current stock {p.get('stock',0)}. Growth uses (recent units − previous units) ÷ previous units × 100; zero previous units means no valid growth percentage."
    elif "selling best by quantity" in q or "highest revenue" in q or "generate the highest revenue" in q or "highest revenue" in q:
        metric = "recent_revenue" if "revenue" in q else "recent_quantity"
        label = "revenue" if metric == "recent_revenue" else "units sold"
        items = sorted(products, key=lambda p: float(p.get(metric,0) or 0), reverse=True)[:5]
        answer = f"Top products by {label} for {period_label}:\n" + product_lines(items, metric, label)
    elif "declining sales" in q:
        items = sorted([p for p in products if p.get('growth_percent') is not None and float(p['growth_percent']) < 0], key=lambda p: float(p['growth_percent']))
        answer = f"Products with negative quantity growth for {period_label}:\n" + product_lines(items)
    elif "increasing sales" in q or "increasing products" in q or "growing products" in q:
        items = sorted([p for p in products if p.get('growth_percent') is not None and float(p['growth_percent']) > 0], key=lambda p: float(p['growth_percent']), reverse=True)
        answer = f"Products with positive quantity growth for {period_label} (new sellers without a baseline are listed separately):\n" + product_lines(items)
    # Marketing planning: evidence-bound recommendations
    elif "promotion budget" in q or "budget" in q and "promot" in q:
        answer = (f"A defensible budget cannot be calculated from sales and stock alone: margins, campaign costs, conversion rates, and budget constraints are missing. "
                  f"For a controlled pilot, set a budget cap with the owner, track spend against attributed revenue and gross margin, and stop if the agreed cap is reached. Recent revenue for {period_label} is {money(overall.get('recent_revenue'))}; it is context, not profit or a safe budget by itself.")
    elif "bundled" in q or "bundle" in q:
        answer = "The available data shows product-level totals, not which products were bought together. I cannot claim a bundle is evidence-based without order/basket-level records containing multiple products per order. Share basket/order IDs to identify frequently co-purchased products; until then, test only a clearly labelled pilot and measure results."
    elif "seven-day marketing plan" in q or "7-day marketing plan" in q or "seven day marketing plan" in q:
        rising = sorted([p for p in products if p.get('growth_percent') is not None and float(p['growth_percent']) > 10 and int(p.get('stock',0) or 0)>5], key=lambda p: float(p['growth_percent']), reverse=True)[:3]
        falling = sorted([p for p in products if p.get('growth_percent') is not None and float(p['growth_percent']) < -10 and int(p.get('stock',0) or 0)>5], key=lambda p: float(p['growth_percent']))[:3]
        answer = ("Seven-day plan based on observed sales and current stock:\nDay 1: Review stock and exclude zero-stock products.\nDay 2: Feature a growing product with stock available: " + (rising[0]['product_name'] if rising else "no qualifying product; review data") + ".\nDay 3: Publish a product-focused post with factual price/availability.\nDay 4: Test a small bundle only as an experiment (basket evidence unavailable).\nDay 5: Test a recovery offer for a declining, in-stock product: " + (falling[0]['product_name'] if falling else "none qualifies") + ".\nDay 6: Check campaign reach, clicks, attributed orders and spend.\nDay 7: Compare campaign-period units/revenue with baseline and keep only measured winners. Do not claim causal lift without campaign attribution.")
    elif "weekend promotion" in q or "weekend" in q and "promotion" in q:
        candidates = sorted([p for p in products if p.get('growth_percent') is not None and float(p['growth_percent']) > 10 and int(p.get('stock',0) or 0)>5], key=lambda p: float(p['growth_percent']), reverse=True)[:2]
        answer = "Weekend promotion based on positive quantity growth and stock above 5 units: " + (", ".join(f"{p['product_name']} ({p['growth_percent']}% growth, stock {p['stock']}, {p['recent_quantity']} recent units)" for p in candidates) if candidates else "no products meet the screening rule; review stock and sales data first") + ". Avoid advertising products with zero stock; monitor attributed orders and revenue during the test."
    elif "not discount" in q or "avoid discount" in q:
        items = sorted([p for p in products if p.get('growth_percent') is not None and float(p['growth_percent']) > 10 and int(p.get('stock',0) or 0) <= 5], key=lambda p: float(p['growth_percent']), reverse=True)
        answer = "Avoid discounting without further review for products already growing strongly but with stock at or below 5 units: " + (", ".join(p['product_name'] for p in items) if items else "no product meets this rule") + ". This is an inventory/sales screening rule, not proof of price elasticity or customer preference."

    if answer is not None:
        return {
            "business_id": business_id, "business_name": business_name,
            "query": query, "answer": answer,
            "intents": [{"intent": "DETERMINISTIC_BUSINESS_ANSWER"}],
            "time_period": {"period_days": period_days, "period_label": period_label, "explicit": period_explicit},
            "analytics": analytics, "rag_context": "",
        }

    # Deterministic aggregate-growth routing must happen before the LLM
    # classifier. This prevents an aggregate question from being mistaken for
    # a request to list increasing products, and avoids an unnecessary Ollama
    # call for a query whose answer is already calculable from PostgreSQL.
    if is_overall_growth_query(query):
        return {
            "business_id": business_id,
            "business_name": business_name,
            "query": query,
            "answer": format_overall_growth_answer(analytics, period_label),
            "intents": [{
                "intent": "OVERALL_GROWTH",
                "metric": "revenue_and_quantity",
                "direction": "comparison",
                "limit": None,
                "product_name": None,
            }],
            "time_period": {
                "period_days": period_days,
                "period_label": period_label,
                "explicit": period_explicit,
            },
            "analytics": analytics,
            "rag_context": "",
        }

    # ========================================================
    # 3. BUILD PRODUCT GROUPS
    # ========================================================

    # Use only the products calculated by the authoritative PostgreSQL analytics
    # for this request's detected period. Do not recalculate growth in the agent.
    increasing_products = [
        p for p in products
        if p.get("growth_percent") is not None
        and float(p.get("growth_percent")) > 0
    ]


    declining_products = [
        p
        for p in products
        if p.get("status") == "Declining"
    ]


    stable_products = [
        p
        for p in products
        if p.get("status") == "Stable"
    ]


    out_of_stock_products = [
        p
        for p in products
        if int(
            p.get("stock", 0) or 0
        ) == 0
    ]


    low_stock_products = [
        p
        for p in products
        if (
            0
            <
            int(
                p.get("stock", 0) or 0
            )
            <= 5
        )
    ]


    # ========================================================
    # 4. SEARCH RAG CONTEXT
    # ========================================================

    rag_results = search_business_context(
        query=query,
        business_id=business_id,
        n_results=3,
    )


    rag_context = build_context(
        rag_results
    )


    # ========================================================
    # 5. CLASSIFY USER QUERY
    # ========================================================

    intents = await classify_query(
        query
    )


    intent_names = {
        intent.get("intent")
        for intent in intents
    }


    # ========================================================
    # HELPER: BUILD STANDARD RESPONSE
    # ========================================================

    def build_response(
        answer: str,
    ) -> Dict[str, Any]:

        return {
            "business_id": business_id,
            "business_name": business_name,
            "query": query,
            "answer": answer,
            "intents": intents,
            "time_period": {
                "period_days": period_days,
                "period_label": period_label,
                "explicit": period_explicit,
            },
            "analytics": analytics,
            "rag_context": rag_context,
        }


    # ========================================================
    # 6. PROFIT
    # ========================================================

    if "PROFIT" in intent_names:

        answer = (
            "Profit cannot currently be calculated accurately "
            "because the available business data does not include "
            "product cost or expense information."
        )

        return build_response(
            answer
        )


    # ========================================================
    # 7. DECLINING + PROMOTION
    #
    # IMPORTANT:
    # This MUST COME BEFORE the generic
    # DECLINING + RECOMMENDATION handler.
    # ========================================================

    if (
        "DECLINING_PRODUCTS" in intent_names
        and
        "PROMOTION_RECOMMENDATION" in intent_names
    ):

        promotion_opportunities = (
            get_declining_promotion_opportunities(
                products,
                limit=5,
            )
        )


        if not promotion_opportunities:

            return build_response(
                "There are currently no declining products "
                "with available inventory that should be "
                "prioritized for promotion."
            )


        answer = (
            "Declining products suitable for promotion:\n\n"
        )


        for index, item in enumerate(
            promotion_opportunities,
            start=1,
        ):

            growth = item.get(
                "growth_percent",
                0,
            )


            growth_text = (
                f"+{growth}%"
                if growth >= 0
                else f"{growth}%"
            )


            answer += (
                f"{index}. {item['product_name']}\n"
                f"   Growth: {growth_text}\n"
                f"   Stock: {item['stock']}\n"
                f"   Recent Revenue: "
                f"₹{item['recent_revenue']}\n"
                f"   Promotion Score: "
                f"{item['promotion_score']}/100\n"
                f"   Priority: "
                f"{item['priority']}\n"
                f"   Reason: "
                f"{item['reason']}\n"
                f"   Recommended Action: "
                f"{item['recommended_action']}\n\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 8. INCREASING + PROMOTION
    # ========================================================

    if (
        "INCREASING_PRODUCTS" in intent_names
        and
        "PROMOTION_RECOMMENDATION" in intent_names
    ):

        promotion_opportunities = (
            get_growing_promotion_opportunities(
                products,
                limit=5,
            )
        )


        if not promotion_opportunities:

            return build_response(
                "There are currently no increasing products "
                "with suitable inventory for promotion."
            )


        answer = (
            "Increasing products suitable for promotion:\n\n"
        )


        for index, item in enumerate(
            promotion_opportunities,
            start=1,
        ):

            growth = item.get(
                "growth_percent",
                0,
            )


            growth_text = (
                f"+{growth}%"
                if growth >= 0
                else f"{growth}%"
            )


            answer += (
                f"{index}. {item['product_name']}\n"
                f"   Growth: {growth_text}\n"
                f"   Stock: {item['stock']}\n"
                f"   Recent Revenue: "
                f"₹{item['recent_revenue']}\n"
                f"   Promotion Score: "
                f"{item['promotion_score']}/100\n"
                f"   Priority: "
                f"{item['priority']}\n"
                f"   Reason: "
                f"{item['reason']}\n"
                f"   Recommended Action: "
                f"{item['recommended_action']}\n\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 9. GENERAL PROMOTION RECOMMENDATION
    #
    # Handles:
    # "Which products should I promote?"
    # "What products have the best promotion opportunity?"
    # "Which products have the best promotion opportunities?"
    #
    # IMPORTANT:
    # General promotion is divided into:
    #
    # 1. Recovery opportunities
    # 2. Growth opportunities
    # 3. Summary
    #
    # This version directly calls the working promotion
    # functions instead of depending on the summary dictionary.
    # ========================================================

    if "PROMOTION_RECOMMENDATION" in intent_names:

        # ----------------------------------------------------
        # RECOVERY OPPORTUNITIES
        # ----------------------------------------------------

        recovery_opportunities = (
            get_declining_promotion_opportunities(
                products,
                limit=5,
            )
        )


        # ----------------------------------------------------
        # GROWTH OPPORTUNITIES
        # ----------------------------------------------------

        growth_opportunities = (
            get_growing_promotion_opportunities(
                products,
                limit=5,
            )
        )


        # ----------------------------------------------------
        # HIGH PRIORITY
        # ----------------------------------------------------

        high_priority = [
            item
            for item in (
                recovery_opportunities
                + growth_opportunities
            )
            if item.get("priority") == "HIGH"
        ]


        # ----------------------------------------------------
        # NO OPPORTUNITIES
        # ----------------------------------------------------

        if (
            not recovery_opportunities
            and
            not growth_opportunities
        ):

            return build_response(
                "There are currently no strong promotion "
                "opportunities based on the available sales "
                "and inventory data."
            )


        # ----------------------------------------------------
        # MAIN RESPONSE
        # ----------------------------------------------------

        answer = (
            f"Promotion Opportunities — {period_label}\n\n"
        )


        # ====================================================
        # RECOVERY OPPORTUNITIES
        # ====================================================

        answer += (
            "RECOVERY OPPORTUNITIES\n"
            "Products whose sales are declining and "
            "could benefit from a targeted recovery campaign.\n\n"
        )


        if recovery_opportunities:

            for index, item in enumerate(
                recovery_opportunities,
                start=1,
            ):

                growth = item.get(
                    "growth_percent",
                    0,
                )


                growth_text = (
                    f"+{growth}%"
                    if growth >= 0
                    else f"{growth}%"
                )


                answer += (
                    f"{index}. {item['product_name']}\n"
                    f"   Growth: {growth_text}\n"
                    f"   Revenue: ₹{item['recent_revenue']}\n"
                    f"   Stock: {item['stock']}\n"
                    f"   Promotion Score: "
                    f"{item['promotion_score']}/100\n"
                    f"   Priority: {item['priority']}\n"
                    f"   Reason: {item['reason']}\n"
                    f"   Action: "
                    f"{item['recommended_action']}\n\n"
                )

        else:

            answer += (
                "No declining products currently qualify "
                "for a recovery promotion.\n\n"
            )


        # ====================================================
        # GROWTH OPPORTUNITIES
        # ====================================================

        answer += (
            "GROWTH OPPORTUNITIES\n"
            "Products already showing positive growth "
            "that could benefit from a growth-focused campaign.\n\n"
        )


        if growth_opportunities:

            for index, item in enumerate(
                growth_opportunities,
                start=1,
            ):

                growth = item.get(
                    "growth_percent",
                    0,
                )


                growth_text = (
                    f"+{growth}%"
                    if growth >= 0
                    else f"{growth}%"
                )


                answer += (
                    f"{index}. {item['product_name']}\n"
                    f"   Growth: {growth_text}\n"
                    f"   Revenue: ₹{item['recent_revenue']}\n"
                    f"   Stock: {item['stock']}\n"
                    f"   Promotion Score: "
                    f"{item['promotion_score']}/100\n"
                    f"   Priority: {item['priority']}\n"
                    f"   Reason: {item['reason']}\n"
                    f"   Action: "
                    f"{item['recommended_action']}\n\n"
                )

        else:

            answer += (
                "No strongly increasing products currently "
                "qualify for a growth promotion.\n\n"
            )


        # ====================================================
        # SUMMARY
        # ====================================================

        answer += (
            "SUMMARY\n"
            f"Recovery opportunities: "
            f"{len(recovery_opportunities)}\n"
            f"Growth opportunities: "
            f"{len(growth_opportunities)}\n"
            f"High-priority opportunities: "
            f"{len(high_priority)}\n"
        )


        return build_response(
            answer
        )


    # ========================================================
    # 10. DECLINING + GENERAL RECOMMENDATION
    # ========================================================

    if (
        "DECLINING_PRODUCTS" in intent_names
        and
        "RECOMMENDATION" in intent_names
    ):

        recommendations = (
            recommend_for_declining_products(
                products
            )
        )


        if not recommendations:

            return build_response(
                "There are currently no declining products "
                "based on the latest sales data."
            )


        answer = (
            "Declining products and recommended actions:\n\n"
        )


        for index, item in enumerate(
            recommendations,
            start=1,
        ):

            answer += (
                f"{index}. {item['product_name']}\n"
                f"   Growth: {item['growth_percent']}%\n"
                f"   Stock: {item['stock']}\n"
                f"   Severity: {item['severity']}\n"
                f"   Action: {item['action']}\n\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 11. INCREASING + GENERAL RECOMMENDATION
    # ========================================================

    if (
        "INCREASING_PRODUCTS" in intent_names
        and
        "RECOMMENDATION" in intent_names
    ):

        recommendations = (
            recommend_for_increasing_products(
                products,
                limit=3,
            )
        )


        if not recommendations:

            return build_response(
                "There are currently no strongly increasing "
                "products based on the latest sales data."
            )


        answer = (
            "Products showing strong growth and "
            "recommended actions:\n\n"
        )


        for index, item in enumerate(
            recommendations,
            start=1,
        ):

            growth = item["growth_percent"]


            growth_text = (
                f"+{growth}%"
                if growth >= 0
                else f"{growth}%"
            )


            answer += (
                f"{index}. {item['product_name']}\n"
                f"   Growth: {growth_text}\n"
                f"   Stock: {item['stock']}\n"
                f"   Severity: {item['severity']}\n"
                f"   Action: {item['action']}\n\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 12. OUT OF STOCK + RECOMMENDATION
    # ========================================================

    if (
        "OUT_OF_STOCK" in intent_names
        and
        (
            "RECOMMENDATION" in intent_names
            or
            "PROMOTION_RECOMMENDATION" in intent_names
        )
    ):

        recommendations = (
            recommend_for_out_of_stock_products(
                products
            )
        )


        if not recommendations:

            return build_response(
                "There are currently no out-of-stock products."
            )


        answer = (
            "Out-of-stock products and recommended actions:\n\n"
        )


        for index, item in enumerate(
            recommendations,
            start=1,
        ):

            answer += (
                f"{index}. {item['product_name']}\n"
                f"   Growth: {item['growth_percent']}%\n"
                f"   Recent sales: "
                f"{item['recent_quantity']} units\n"
                f"   Recent revenue: "
                f"₹{item['recent_revenue']}\n"
                f"   Severity: {item['severity']}\n"
                f"   Action: {item['action']}\n\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 13. OUT OF STOCK ONLY
    # ========================================================

    if "OUT_OF_STOCK" in intent_names:

        if not out_of_stock_products:

            return build_response(
                "There are currently no out-of-stock products."
            )


        answer = (
            f"Products currently out of stock for {business_name}:\n\n"
        )

        for index, product in enumerate(out_of_stock_products, start=1):
            answer += (
                f"{index}. {product['product_name']}\n"
                f"   Current stock: {int(product.get('stock', 0) or 0)}\n\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 14. LOW STOCK
    # ========================================================

    if "LOW_STOCK" in intent_names:

        if not low_stock_products:

            return build_response(
                "There are currently no products with low stock."
            )


        answer = (
            "Products with low stock:\n\n"
        )


        for index, product in enumerate(
            low_stock_products,
            start=1,
        ):

            answer += (
                f"{index}. {product['product_name']}\n"
                f"   Stock: "
                f"{product.get('stock', 0)}\n"
                f"   Growth: "
                f"{product.get('growth_percent')}%\n"
                f"   Status: "
                f"{product.get('status')}\n\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 15. NEEDS ATTENTION
    # ========================================================

    if "NEEDS_ATTENTION" in intent_names:

        attention_products = [
            p
            for p in products
            if (
                p.get("status") == "Declining"
                or
                int(
                    p.get("stock", 0) or 0
                ) == 0
                or
                (
                    0
                    <
                    int(
                        p.get("stock", 0) or 0
                    )
                    <= 5
                )
            )
        ]


        # ----------------------------------------------------
        # Remove duplicates
        # ----------------------------------------------------

        unique_products = {}


        for product in attention_products:

            unique_products[
                product["product_name"]
            ] = product


        attention_products = list(
            unique_products.values()
        )


        if not attention_products:

            return build_response(
                "No products currently require immediate attention."
            )


        # ----------------------------------------------------
        # Worst growth first
        # ----------------------------------------------------

        attention_products.sort(
            key=lambda x: (
                x.get("growth_percent")
                if x.get("growth_percent") is not None
                else 0
            )
        )


        answer = (
            "Products that need attention:\n\n"
        )


        for index, product in enumerate(
            attention_products,
            start=1,
        ):

            recommendation = (
                get_product_recommendation(
                    product
                )
            )


            answer += (
                f"{index}. {product['product_name']}\n"
                f"   Growth: "
                f"{product.get('growth_percent')}%\n"
                f"   Stock: "
                f"{product.get('stock', 0)}\n"
                f"   Severity: "
                f"{recommendation['severity']}\n"
                f"   Action: "
                f"{recommendation['action']}\n\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 16. DECLINING PRODUCTS ONLY
    # ========================================================

    if "DECLINING_PRODUCTS" in intent_names:

        if not declining_products:

            return build_response(
                "There are currently no declining products."
            )


        declining_products.sort(
            key=lambda x: (
                x.get("growth_percent")
                if x.get("growth_percent") is not None
                else 0
            )
        )


        answer = (
            f"Products with declining sales for {period_label} "
            f"compared with the preceding {period_days} days:\n\n"
        )


        for index, product in enumerate(
            declining_products,
            start=1,
        ):

            answer += (
                f"{index}. {product['product_name']}\n"
                f"   Growth: "
                f"{product.get('growth_percent')}%\n"
                f"   Stock: "
                f"{product.get('stock', 0)}\n"
                f"   Revenue: "
                f"₹{product.get('recent_revenue', 0)}\n\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 17. INCREASING PRODUCTS ONLY
    # ========================================================

    if "INCREASING_PRODUCTS" in intent_names:

        if not increasing_products:

            return build_response(
                f"No products have positive quantity growth for {period_label} "
                f"compared with the preceding {period_days} days, or the "
                "previous-period baseline is unavailable."
            )


        increasing_products.sort(
            key=lambda x: (
                x.get("growth_percent")
                if x.get("growth_percent") is not None
                else 0
            ),
            reverse=True,
        )


        answer = (
            f"Products showing increasing sales for {period_label} "
            f"compared with the preceding {period_days} days:\n\n"
        )


        for index, product in enumerate(
            increasing_products,
            start=1,
        ):

            growth = float(product["growth_percent"])
            answer += (
                f"{index}. {product['product_name']}\n"
                f"   Quantity growth: +{growth:.2f}%\n"
                f"   Units sold in recent period: "
                f"{product.get('recent_quantity', 0)}\n"
                f"   Current stock: {int(product.get('stock', 0) or 0)}\n"
                f"   Revenue in recent period: "
                f"₹{float(product.get('recent_revenue', 0) or 0):,.2f}\n\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 18. FOCUS PRODUCTS
    # ========================================================

    if "FOCUS_PRODUCTS" in intent_names:

        focus_products = [
            p
            for p in products
            if p.get("status") == "Increasing"
        ]


        focus_products.sort(
            key=lambda x: (
                x.get("growth_percent")
                if x.get("growth_percent") is not None
                else 0
            ),
            reverse=True,
        )


        focus_products = focus_products[:3]


        if not focus_products:

            return build_response(
                "There are currently no strongly increasing "
                "products to prioritize."
            )


        answer = (
            "Products you should consider focusing on:\n\n"
        )


        for index, product in enumerate(
            focus_products,
            start=1,
        ):

            recommendation = (
                get_product_recommendation(
                    product
                )
            )


            answer += (
                f"{index}. {product['product_name']}\n"
                f"   Growth: "
                f"+{product.get('growth_percent')}%\n"
                f"   Stock: "
                f"{product.get('stock', 0)}\n"
                f"   Action: "
                f"{recommendation['action']}\n\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 19. PRODUCT RANKING
    # ========================================================

    if "PRODUCT_RANKING" in intent_names:

        ranking_intent = next(
            (
                intent
                for intent in intents
                if intent.get("intent")
                == "PRODUCT_RANKING"
            ),
            {},
        )


        metric = ranking_intent.get(
            "metric",
            "revenue",
        )


        direction = ranking_intent.get(
            "direction",
            "highest",
        )


        limit = ranking_intent.get(
            "limit"
        )


        if limit is None:

            limit = 5


        # ----------------------------------------------------
        # Revenue
        # ----------------------------------------------------

        if metric == "revenue":

            sorted_products = sorted(
                products,
                key=lambda x: float(
                    x.get(
                        "recent_revenue",
                        0,
                    )
                    or 0
                ),
                reverse=(
                    direction != "lowest"
                ),
            )


            metric_label = "recent revenue"


        # ----------------------------------------------------
        # Quantity
        # ----------------------------------------------------

        elif metric == "quantity":

            sorted_products = sorted(
                products,
                key=lambda x: int(
                    x.get(
                        "recent_quantity",
                        0,
                    )
                    or 0
                ),
                reverse=(
                    direction != "lowest"
                ),
            )


            metric_label = "recent units sold"


        # ----------------------------------------------------
        # Growth
        # ----------------------------------------------------

        elif metric == "growth":

            sorted_products = sorted(
                products,
                key=lambda x: (
                    x.get("growth_percent")
                    if x.get("growth_percent")
                    is not None
                    else 0
                ),
                reverse=(
                    direction != "lowest"
                ),
            )


            metric_label = "recent growth"


        else:

            sorted_products = products

            metric_label = "performance"


        sorted_products = sorted_products[
            :limit
        ]


        if not sorted_products:

            return build_response(
                "No product performance data is currently available."
            )


        # ----------------------------------------------------
        # Single result
        # ----------------------------------------------------

        if limit == 1:

            product = sorted_products[0]


            if metric == "revenue":

                value = (
                    f"₹{product.get('recent_revenue', 0)}"
                )


            elif metric == "quantity":

                value = (
                    f"{product.get('recent_quantity', 0)} units"
                )


            else:

                value = (
                    f"{product.get('growth_percent')}%"
                )


            direction_text = (
                "highest"
                if direction != "lowest"
                else "lowest"
            )


            answer = (
                f"{product['product_name']} has the "
                f"{direction_text} {metric_label}: "
                f"{value}."
            )


            return build_response(
                answer
            )


        # ----------------------------------------------------
        # Multiple results
        # ----------------------------------------------------

        direction_text = (
            "highest"
            if direction != "lowest"
            else "lowest"
        )


        answer = (
            f"Products with the {direction_text} "
            f"{metric_label}:\n\n"
        )


        for index, product in enumerate(
            sorted_products,
            start=1,
        ):

            if metric == "revenue":

                value = (
                    f"₹{product.get('recent_revenue', 0)}"
                )


            elif metric == "quantity":

                value = (
                    f"{product.get('recent_quantity', 0)} units"
                )


            else:

                value = (
                    f"{product.get('growth_percent')}%"
                )


            answer += (
                f"{index}. "
                f"{product['product_name']} — "
                f"{value}\n"
            )


        return build_response(
            answer
        )


    # ========================================================
    # 20. SALES SUMMARY
    # ========================================================

    if "SALES_SUMMARY" in intent_names:

        recent_quantity = analytics.get(
            "recent_quantity",
            0,
        )


        previous_quantity = analytics.get(
            "previous_quantity",
            0,
        )


        quantity_growth = analytics.get(
            "quantity_growth_percent"
        )


        answer = (
            f"Sales summary for {business_name} "
            f"over {period_label}:\n\n"
            f"Recent units sold: {recent_quantity}\n"
            f"Previous units sold: {previous_quantity}\n"
            f"Quantity growth: {quantity_growth}%"
        )


        return build_response(
            answer
        )


    # ========================================================
    # 21. REVENUE SUMMARY
    # ========================================================

    if "REVENUE_SUMMARY" in intent_names:

        recent_revenue = analytics.get(
            "recent_revenue",
            0,
        )


        previous_revenue = analytics.get(
            "previous_revenue",
            0,
        )


        revenue_growth = analytics.get(
            "revenue_growth_percent"
        )


        answer = (
            f"Revenue summary for {business_name} "
            f"over {period_label}:\n\n"
            f"Recent revenue: ₹{recent_revenue}\n"
            f"Previous revenue: ₹{previous_revenue}\n"
            f"Revenue growth: {revenue_growth}%"
        )


        return build_response(
            answer
        )


    # ========================================================
    # 22. GENERAL RECOMMENDATION
    # ========================================================

    if "RECOMMENDATION" in intent_names:

        recommendations = (
            generate_business_recommendations(
                analytics
            )
        )


        critical = recommendations.get(
            "critical",
            [],
        )


        high = recommendations.get(
            "high",
            [],
        )


        medium = recommendations.get(
            "medium",
            [],
        )


        if critical:

            answer = (
                "The business currently has critical issues "
                "that should be reviewed first:\n\n"
            )


            for item in critical[:5]:

                answer += (
                    f"• {item['product_name']} — "
                    f"{item['action']}\n"
                )


            return build_response(
                answer
            )


        if high:

            answer = (
                "The following areas require attention:\n\n"
            )


            for item in high[:5]:

                answer += (
                    f"• {item['product_name']} — "
                    f"{item['action']}\n"
                )


            return build_response(
                answer
            )


        if medium:

            answer = (
                "The business has several growth opportunities:\n\n"
            )


            for item in medium[:5]:

                answer += (
                    f"• {item['product_name']} — "
                    f"{item['action']}\n"
                )


            return build_response(
                answer
            )


        return build_response(
            "The current product performance is generally stable. "
            "Continue monitoring sales and inventory."
        )


    # ========================================================
    # 23. SPECIFIC PRODUCT QUESTION
    # ========================================================

    query_lower = query.lower()


    matched_product = None


    for product in products:

        product_name = product.get(
            "product_name",
            "",
        )


        if product_name.lower() in query_lower:

            matched_product = product

            break


    if matched_product:

        recommendation = (
            get_product_recommendation(
                matched_product
            )
        )


        answer = (
            f"{matched_product['product_name']} performance:\n\n"
            f"Period: {period_label}\n"
            f"Recent units sold: "
            f"{matched_product.get('recent_quantity', 0)}\n"
            f"Recent revenue: "
            f"₹{matched_product.get('recent_revenue', 0)}\n"
            f"Growth: "
            f"{matched_product.get('growth_percent')}%\n"
            f"Stock: "
            f"{matched_product.get('stock', 0)}\n"
            f"Status: "
            f"{matched_product.get('status')}\n\n"
            f"Recommendation: "
            f"{recommendation['action']}"
        )


        return build_response(
            answer
        )


    # ========================================================
    # 24. GENERAL LLM FALLBACK
    # ========================================================

    prompt = f"""
You are a business analytics assistant for {business_name}.

You must answer the user's question using only the verified
business information provided below.

=========================================================
TIME PERIOD
=========================================================

The verified analytics represent:

{period_label}

=========================================================
VERIFIED BUSINESS ANALYTICS
=========================================================

{analytics}

=========================================================
RELEVANT BUSINESS CONTEXT
=========================================================

{rag_context}

=========================================================
USER QUESTION
=========================================================

{query}

=========================================================
STRICT RULES
=========================================================

1. PostgreSQL analytics is the authoritative source for
   sales, revenue, growth and stock.

2. Never invent sales numbers.

3. Never invent revenue.

4. Never invent stock levels.

5. Never invent growth percentages.

6. Never invent product performance.

7. Never invent business facts.

8. Never treat revenue as profit.

9. Profit cannot be determined unless cost data exists.

10. Never invent reasons for sales changes.

11. Never claim that a campaign caused sales changes unless
    verified campaign-performance data exists.

12. If the available data does not support an answer,
    clearly say that the required information is not available.

13. The analytics period is {period_label}.

14. Keep the answer concise and factual.

Give a direct answer to the user's question.
"""


    try:

        llm_answer = await generate_response(
            prompt
        )

    except Exception:

        llm_answer = (
            "I could not generate an answer from the available "
            "business data."
        )


    return build_response(
        llm_answer.strip()
    )


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

# If any other part of the project uses run_business_agent,
# it will continue to work.

run_business_agent = ask_business_agent