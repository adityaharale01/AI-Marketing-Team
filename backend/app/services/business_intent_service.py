def detect_business_intent(query: str) -> str:

    query_lower = query.lower().strip()

    # =====================================================
    # PROFIT
    # =====================================================

    profit_keywords = [
        "profit",
        "profitability",
        "profit margin",
        "net profit",
        "gross profit",
        "earnings"
    ]

    if any(keyword in query_lower for keyword in profit_keywords):
        return "profit"

    # =====================================================
    # OUT OF STOCK
    # =====================================================

    out_of_stock_keywords = [
        "out of stock",
        "no stock",
        "stock is zero",
        "stock 0",
        "zero stock"
    ]

    if any(
        keyword in query_lower
        for keyword in out_of_stock_keywords
    ):
        return "out_of_stock"

    # =====================================================
    # LOW STOCK
    # =====================================================

    low_stock_keywords = [
        "low stock",
        "low inventory",
        "running low",
        "need restocking",
        "needs restocking"
    ]

    if any(
        keyword in query_lower
        for keyword in low_stock_keywords
    ):
        return "low_stock"

    # =====================================================
    # DECLINING
    # =====================================================

    declining_keywords = [
        "declining",
        "decline",
        "decreasing",
        "decrease",
        "falling",
        "fall",
        "dropping",
        "drop",
        "need attention",
        "needs attention"
    ]

    if any(
        keyword in query_lower
        for keyword in declining_keywords
    ):
        return "declining"

    # =====================================================
    # INCREASING
    # =====================================================

    increasing_keywords = [
        "increasing",
        "increase",
        "growing",
        "growth",
        "improving",
        "improvement"
    ]

    if any(
        keyword in query_lower
        for keyword in increasing_keywords
    ):
        return "increasing"

    # =====================================================
    # PERFORMING
    # =====================================================

    performing_keywords = [
        "performing well",
        "performing best",
        "best product",
        "top product",
        "best selling",
        "best-selling",
        "perform well",
        "performing"
    ]

    if any(
        keyword in query_lower
        for keyword in performing_keywords
    ):
        return "performing"

    # =====================================================
    # SALES SUMMARY
    # =====================================================

    sales_summary_keywords = [
        "sales summary",
        "sales performance",
        "how are my sales",
        "how is my sales",
        "sales doing",
        "revenue summary",
        "sales report",
        "sales overview",
        "business performance"
    ]

    if any(
        keyword in query_lower
        for keyword in sales_summary_keywords
    ):
        return "sales_summary"

    # =====================================================
    # TOP PRODUCTS
    # =====================================================

    top_product_keywords = [
        "top products",
        "top selling products",
        "top-selling products",
        "highest revenue",
        "highest sales",
        "most sold",
        "most selling products"
    ]

    if any(
        keyword in query_lower
        for keyword in top_product_keywords
    ):
        return "top_products"

    # =====================================================
    # GENERAL
    # =====================================================

    return "general"