from app.services.business_analytics_service import (
    get_business_analytics
)

from app.services.rag_service import (
    search_business_context,
    build_context
)

from app.services.ollama_service import (
    generate_response
)


async def ask_business_agent(
    db,
    business_id: int,
    query: str
):

    # =========================================================
    # 1. GET VERIFIED BUSINESS ANALYTICS FROM POSTGRESQL
    # =========================================================

    analytics = get_business_analytics(
        db,
        business_id
    )

    # =========================================================
    # 2. HANDLE BUSINESS WITH NO SALES DATA
    # =========================================================

    if "message" in analytics:

        return {
            "business_id": business_id,
            "business_name": analytics["business_name"],
            "query": query,
            "answer": analytics["message"],
            "analytics": analytics
        }

    # =========================================================
    # 3. CREATE VERIFIED FINDINGS
    # =========================================================

    verified_findings = []

    for product in analytics.get("products", []):

        # -----------------------------------------------------
        # Stock status
        # -----------------------------------------------------

        if product["stock"] == 0:
            stock_status = "Out of stock"

        elif product["stock"] <= 5:
            stock_status = "Low stock"

        else:
            stock_status = "In stock"

        # -----------------------------------------------------
        # Verified finding
        # -----------------------------------------------------

        finding = {
            "product_name": product["product_name"],
            "recent_quantity": product["recent_quantity"],
            "recent_revenue": product["recent_revenue"],
            "previous_quantity": product["previous_quantity"],
            "growth_percent": product["growth_percent"],
            "performance_label": product["performance_label"],
            "stock": product["stock"],
            "stock_status": stock_status,
            "status": product["status"]
        }

        verified_findings.append(finding)

    # =========================================================
    # 4. DETERMINE PRODUCT COMPARISON
    # =========================================================

    comparison_possible = (
        len(verified_findings) > 1
    )

    if not comparison_possible:

        comparison_instruction = """
There is only one product with available sales data.

A product-to-product comparison is NOT possible.

Do NOT identify the product as the best-performing
product.

Explain only the verified facts.
"""

    else:

        comparison_instruction = """
Multiple products are available.

Only identify a best-performing product if the
verified analytics supports the comparison.
"""

    # =========================================================
    # 5. SEARCH BUSINESS-SPECIFIC RAG CONTEXT
    # =========================================================

    rag_results = search_business_context(
        query=query,
        business_id=business_id,
        n_results=3
    )

    rag_context = build_context(
        rag_results
    )

    # =========================================================
    # 6. PERFORMANCE QUESTION DETECTION
    # =========================================================

    performance_keywords = [
        "performing well",
        "performing best",
        "best product",
        "top product",
        "best selling",
        "best-selling",
        "which product is better",
        "which product performs best",
        "which product is performing best"
    ]

    query_lower = query.lower()

        # =========================================================
    # HANDLE QUESTIONS ABOUT UNAVAILABLE PROFIT DATA
    # =========================================================

    profit_keywords = [
        "profit",
        "profitability",
        "profit margin",
        "net profit",
        "gross profit",
        "earnings"
    ]

    is_profit_question = any(
        keyword in query_lower
        for keyword in profit_keywords
    )

    if is_profit_question:

        answer = (
            "Profit cannot be determined from the available "
            "business data because the system currently stores "
            "sales revenue but does not contain product cost "
            "or profit data."
        )

        return {
            "business_id": business_id,
            "business_name": analytics["business_name"],
            "query": query,
            "answer": answer,
            "analytics": analytics,
            "rag_context": rag_context
        }

    is_performance_comparison = any(
        keyword in query_lower
        for keyword in performance_keywords
    )

    # =========================================================
    # 7. HANDLE UNSUPPORTED COMPARISON
    # =========================================================

    if (
        is_performance_comparison
        and len(verified_findings) < 2
    ):

        answer = (
            "The available data is insufficient to determine "
            "which product is performing best because only "
            "one product has available sales data."
        )

        return {
            "business_id": business_id,
            "business_name": analytics["business_name"],
            "query": query,
            "answer": answer,
            "analytics": analytics,
            "rag_context": rag_context
        }

    # =========================================================
    # 8. CREATE GROUNDED LLM PROMPT
    # =========================================================

    prompt = f"""
You are the Business Agent of an AI Marketing Team.

Your job is to answer the business owner's question using
verified business data.

{comparison_instruction}

=========================================================
VERIFIED BUSINESS ANALYTICS
SOURCE: PostgreSQL
=========================================================

{analytics}

=========================================================
VERIFIED FINDINGS
=========================================================

{verified_findings}

=========================================================
BUSINESS KNOWLEDGE
SOURCE: ChromaDB RAG
=========================================================

{rag_context}

=========================================================
BUSINESS OWNER QUESTION
=========================================================

{query}

=========================================================
STRICT RULES
=========================================================

1. Use only information provided in the analytics,
   verified findings, and RAG context.

2. PostgreSQL analytics is the authoritative source
   for numerical sales, revenue, growth and stock data.

3. RAG context provides additional business information,
   such as product descriptions, campaigns and business
   information.

4. Never invent facts.

5. Never infer customer demand unless an explicit demand
   metric is provided.

6. Never calculate growth yourself.

7. If growth_percent is null, say that growth cannot
   be determined because there is no previous baseline.

8. Never call a product "best" unless enough data exists
   for a valid comparison.

9. If only one product has sales data, do not compare
   it with other products.

10. If stock is 0, explicitly say that the product is
    currently out of stock.

11. If stock is between 1 and 5, explicitly say that
    the product has low stock.

12. Never say a product is in stock when stock is 0.

13. Do not invent reasons for sales, revenue, growth,
    stock levels or customer behavior.

14. Do not treat campaign information as proof of sales
    performance.

15. Use ₹ when referring to revenue or prices.

16. If information is not available, clearly say that
    it cannot be determined from the available data.

17. Keep the answer concise and business-focused.

=========================================================

Provide the final factual answer to the business owner.
"""

    # =========================================================
    # 9. GENERATE ANSWER USING LOCAL LLAMA
    # =========================================================

    answer = await generate_response(
        prompt
    )

    # =========================================================
    # 10. RETURN COMPLETE BUSINESS AGENT RESPONSE
    # =========================================================

    return {
        "business_id": business_id,
        "business_name": analytics["business_name"],
        "query": query,
        "answer": answer,
        "analytics": analytics,
        "rag_context": rag_context
    }