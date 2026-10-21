from typing import Dict, List, Any


def get_product_recommendation(product: dict) -> Dict[str, Any]:
    """
    Generate a business recommendation from verified product analytics.

    This function does NOT invent sales data.
    All decisions are based on:
    - growth_percent
    - stock
    - status
    - recent_revenue
    - recent_quantity
    """

    name = product.get("product_name", "Product")

    growth = product.get("growth_percent")
    stock = product.get("stock", 0)
    status = product.get("status", "Stable")

    recent_revenue = product.get("recent_revenue", 0)
    recent_quantity = product.get("recent_quantity", 0)

    # Safe numeric conversion
    growth = float(growth) if growth is not None else 0.0
    stock = int(stock or 0)
    recent_revenue = float(recent_revenue or 0)
    recent_quantity = int(recent_quantity or 0)

    # ---------------------------------------------------------
    # 1. CRITICAL: DECLINING + OUT OF STOCK
    # ---------------------------------------------------------
    if status == "Declining" and stock == 0:

        return {
            "product_name": name,
            "severity": "CRITICAL",
            "growth_percent": growth,
            "stock": stock,
            "recent_revenue": recent_revenue,
            "recent_quantity": recent_quantity,
            "action": (
                "Sales are declining and the product is currently out of stock. "
                "Investigate the reason for the sales decline before placing a "
                "large restocking order."
            ),
            "reason": (
                f"Sales declined by {growth}% and current stock is 0."
            )
        }

    # ---------------------------------------------------------
    # 2. HIGH: INCREASING + OUT OF STOCK
    # ---------------------------------------------------------
    if status == "Increasing" and stock == 0:

        return {
            "product_name": name,
            "severity": "HIGH",
            "growth_percent": growth,
            "stock": stock,
            "recent_revenue": recent_revenue,
            "recent_quantity": recent_quantity,
            "action": (
                "Sales are increasing but the product is out of stock. "
                "Prioritize restocking to avoid losing potential sales."
            ),
            "reason": (
                f"Sales increased by {growth}% while stock is 0."
            )
        }

    # ---------------------------------------------------------
    # 3. HIGH: DECLINING + LOW STOCK
    # ---------------------------------------------------------
    if status == "Declining" and 0 < stock <= 5:

        return {
            "product_name": name,
            "severity": "HIGH",
            "growth_percent": growth,
            "stock": stock,
            "recent_revenue": recent_revenue,
            "recent_quantity": recent_quantity,
            "action": (
                "Sales are declining and inventory is already low. "
                "Review recent demand before replenishing and consider a "
                "targeted promotion if the product remains strategically important."
            ),
            "reason": (
                f"Sales declined by {growth}% and only {stock} units remain."
            )
        }

    # ---------------------------------------------------------
    # 4. HIGH: DECLINING + NORMAL STOCK
    # ---------------------------------------------------------
    if status == "Declining":

        return {
            "product_name": name,
            "severity": "HIGH",
            "growth_percent": growth,
            "stock": stock,
            "recent_revenue": recent_revenue,
            "recent_quantity": recent_quantity,
            "action": (
                "Sales are declining while inventory is available. "
                "Review recent demand and consider a targeted promotional "
                "campaign before increasing inventory."
            ),
            "reason": (
                f"Sales declined by {growth}% with {stock} units in stock."
            )
        }

    # ---------------------------------------------------------
    # 5. HIGH: INCREASING + LOW STOCK
    # ---------------------------------------------------------
    if status == "Increasing" and 0 < stock <= 5:

        return {
            "product_name": name,
            "severity": "HIGH",
            "growth_percent": growth,
            "stock": stock,
            "recent_revenue": recent_revenue,
            "recent_quantity": recent_quantity,
            "action": (
                "Sales are increasing and inventory is low. "
                "Consider restocking soon and maintain product availability."
            ),
            "reason": (
                f"Sales increased by {growth}% and only {stock} units remain."
            )
        }

    # ---------------------------------------------------------
    # 6. MEDIUM: INCREASING + NORMAL STOCK
    # ---------------------------------------------------------
    if status == "Increasing":

        return {
            "product_name": name,
            "severity": "MEDIUM",
            "growth_percent": growth,
            "stock": stock,
            "recent_revenue": recent_revenue,
            "recent_quantity": recent_quantity,
            "action": (
                "Sales are increasing. Maintain sufficient inventory and "
                "consider targeted promotion to capitalize on the positive trend."
            ),
            "reason": (
                f"Sales increased by {growth}% with {stock} units in stock."
            )
        }

    # ---------------------------------------------------------
    # 7. MEDIUM: STABLE + LOW STOCK
    # ---------------------------------------------------------
    if status == "Stable" and 0 < stock <= 5:

        return {
            "product_name": name,
            "severity": "MEDIUM",
            "growth_percent": growth,
            "stock": stock,
            "recent_revenue": recent_revenue,
            "recent_quantity": recent_quantity,
            "action": (
                "Sales are stable but inventory is low. "
                "Monitor demand and consider replenishing inventory soon."
            ),
            "reason": (
                f"Sales are stable and only {stock} units remain."
            )
        }

    # ---------------------------------------------------------
    # 8. LOW: STABLE + NORMAL STOCK
    # ---------------------------------------------------------
    return {
        "product_name": name,
        "severity": "LOW",
        "growth_percent": growth,
        "stock": stock,
        "recent_revenue": recent_revenue,
        "recent_quantity": recent_quantity,
        "action": (
            "Sales are currently stable. Continue monitoring sales and "
            "inventory performance."
        ),
        "reason": (
            f"Sales are currently stable with {stock} units in stock."
        )
    }


# =============================================================
# DECLINING PRODUCTS
# =============================================================

def recommend_for_declining_products(
    products: List[dict]
) -> List[Dict[str, Any]]:

    declining = [
        product
        for product in products
        if product.get("status") == "Declining"
    ]

    # Worst decline first
    declining.sort(
        key=lambda x: (
            x.get("growth_percent")
            if x.get("growth_percent") is not None
            else 0
        )
    )

    return [
        get_product_recommendation(product)
        for product in declining
    ]


# =============================================================
# INCREASING PRODUCTS
# =============================================================

def recommend_for_increasing_products(
    products: List[dict],
    limit: int = 3
) -> List[Dict[str, Any]]:

    increasing = [
        product
        for product in products
        if product.get("status") == "Increasing"
    ]

    # Highest growth first
    increasing.sort(
        key=lambda x: (
            x.get("growth_percent")
            if x.get("growth_percent") is not None
            else 0
        ),
        reverse=True
    )

    return [
        get_product_recommendation(product)
        for product in increasing[:limit]
    ]


# =============================================================
# OUT OF STOCK
# =============================================================

def recommend_for_out_of_stock_products(
    products: List[dict]
) -> List[Dict[str, Any]]:

    out_of_stock = [
        product
        for product in products
        if int(product.get("stock", 0) or 0) == 0
    ]

    return [
        get_product_recommendation(product)
        for product in out_of_stock
    ]


# =============================================================
# LOW STOCK
# =============================================================

def recommend_for_low_stock_products(
    products: List[dict]
) -> List[Dict[str, Any]]:

    low_stock = [
        product
        for product in products
        if 0 < int(product.get("stock", 0) or 0) <= 5
    ]

    return [
        get_product_recommendation(product)
        for product in low_stock
    ]


# =============================================================
# COMPLETE BUSINESS RECOMMENDATIONS
# =============================================================

def generate_business_recommendations(
    analytics: dict
) -> Dict[str, Any]:

    products = analytics.get("products", [])

    recommendations = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
    }

    # Generate recommendations for every product
    for product in products:

        recommendation = get_product_recommendation(product)

        severity = recommendation["severity"].lower()

        recommendations.setdefault(severity, [])

        recommendations[severity].append(
            recommendation
        )

    # Sort important recommendations first
    recommendations["critical"].sort(
        key=lambda x: x.get("growth_percent", 0)
    )

    recommendations["high"].sort(
        key=lambda x: x.get("growth_percent", 0)
    )

    recommendations["medium"].sort(
        key=lambda x: x.get("growth_percent", 0),
        reverse=True
    )

    return recommendations