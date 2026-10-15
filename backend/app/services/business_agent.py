# app/services/business_agent.py

from typing import Any, Dict, List

from sqlalchemy.orm import Session


from app.services.business_analytics_service import (
    get_business_analytics,
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


    # ========================================================
    # 3. BUILD PRODUCT GROUPS
    # ========================================================

    increasing_products = [
        p
        for p in products
        if p.get("status") == "Increasing"
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
            "The following products are currently "
            "out of stock:\n\n"
        )


        for index, product in enumerate(
            out_of_stock_products,
            start=1,
        ):

            answer += (
                f"{index}. {product['product_name']}\n"
                f"   Growth: "
                f"{product.get('growth_percent')}%\n"
                f"   Recent quantity: "
                f"{product.get('recent_quantity', 0)} units\n"
                f"   Recent revenue: "
                f"₹{product.get('recent_revenue', 0)}\n\n"
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
            "Products with declining sales:\n\n"
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
                "There are currently no increasing products."
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
            "Products showing increasing sales:\n\n"
        )


        for index, product in enumerate(
            increasing_products,
            start=1,
        ):

            answer += (
                f"{index}. {product['product_name']}\n"
                f"   Growth: "
                f"+{product.get('growth_percent')}%\n"
                f"   Stock: "
                f"{product.get('stock', 0)}\n"
                f"   Revenue: "
                f"₹{product.get('recent_revenue', 0)}\n\n"
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