from typing import Any, Dict, List


# ============================================================
# PROMOTION TYPES
# ============================================================

RECOVERY = "RECOVERY"
GROWTH = "GROWTH"
GENERAL = "GENERAL"


# ============================================================
# PRIORITY
# ============================================================

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
NOT_RECOMMENDED = "NOT_RECOMMENDED"


# ============================================================
# HELPER
# ============================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default

        return int(value)

    except (TypeError, ValueError):
        return default


# ============================================================
# PROMOTION SCORE
# ============================================================

def calculate_promotion_score(
    growth_percent: float,
    stock: int,
    recent_revenue: float,
    recent_quantity: int,
) -> int:

    score = 0

    # --------------------------------------------------------
    # Growth / decline
    # --------------------------------------------------------

    if growth_percent <= -50:
        score += 40

    elif growth_percent <= -30:
        score += 30

    elif growth_percent <= -10:
        score += 20

    elif growth_percent >= 50:
        score += 30

    elif growth_percent >= 30:
        score += 25

    elif growth_percent >= 20:
        score += 20

    elif growth_percent > 10:
        score += 15

    # --------------------------------------------------------
    # Stock
    # --------------------------------------------------------

    if stock == 0:

        return 0

    elif stock <= 5:

        score -= 15

    elif stock <= 15:

        score += 5

    elif stock <= 30:

        score += 15

    else:

        score += 20

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    if recent_revenue >= 100000:

        score += 20

    elif recent_revenue >= 50000:

        score += 15

    elif recent_revenue >= 20000:

        score += 10

    elif recent_revenue >= 10000:

        score += 7

    elif recent_revenue >= 5000:

        score += 5

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    if recent_quantity >= 50:

        score += 15

    elif recent_quantity >= 40:

        score += 10

    elif recent_quantity >= 25:

        score += 5

    return max(0, min(score, 100))


# ============================================================
# PRIORITY
# ============================================================

def get_priority(score: int) -> str:

    if score >= 60:

        return HIGH

    if score >= 40:

        return MEDIUM

    if score >= 20:

        return LOW

    return NOT_RECOMMENDED


# ============================================================
# PROMOTION TYPE
# ============================================================

def get_promotion_type(
    growth_percent: float,
) -> str:

    if growth_percent < -10:

        return RECOVERY

    if growth_percent > 10:

        return GROWTH

    return GENERAL


# ============================================================
# PROMOTION REASON
# ============================================================

def build_promotion_reason(
    growth_percent: float,
    stock: int,
    recent_revenue: float,
) -> str:

    reasons = []

    # --------------------------------------------------------
    # Growth
    # --------------------------------------------------------

    if growth_percent <= -30:

        reasons.append(
            "sales are showing a strong decline"
        )

    elif growth_percent < -10:

        reasons.append(
            "sales are declining"
        )

    elif growth_percent >= 30:

        reasons.append(
            "sales are showing strong growth"
        )

    elif growth_percent > 10:

        reasons.append(
            "sales are showing positive growth"
        )

    else:

        reasons.append(
            "sales are relatively stable"
        )

    # --------------------------------------------------------
    # Stock
    # --------------------------------------------------------

    if stock == 0:

        reasons.append(
            "the product is currently out of stock"
        )

    elif stock <= 5:

        reasons.append(
            "inventory is limited"
        )

    elif stock >= 15:

        reasons.append(
            "sufficient inventory is available"
        )

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    if recent_revenue >= 50000:

        reasons.append(
            "the product contributes significant recent revenue"
        )

    elif recent_revenue >= 20000:

        reasons.append(
            "the product contributes meaningful recent revenue"
        )

    return (
        "The product is a promotion opportunity because "
        + ", ".join(reasons)
        + "."
    )


# ============================================================
# RECOMMENDED ACTION
# ============================================================

def build_promotion_action(
    growth_percent: float,
    stock: int,
) -> str:

    # --------------------------------------------------------
    # Out of stock
    # --------------------------------------------------------

    if stock == 0:

        return (
            "Do not run a promotion until inventory is "
            "restocked."
        )

    # --------------------------------------------------------
    # Severe decline
    # --------------------------------------------------------

    if growth_percent <= -50:

        return (
            "Run a targeted recovery campaign with a "
            "limited-time offer and closely monitor sales "
            "response."
        )

    # --------------------------------------------------------
    # Strong decline
    # --------------------------------------------------------

    if growth_percent <= -30:

        return (
            "Run a targeted recovery promotion and monitor "
            "sales response before making inventory decisions."
        )

    # --------------------------------------------------------
    # Moderate decline
    # --------------------------------------------------------

    if growth_percent < -10:

        return (
            "Run a targeted promotional campaign to recover "
            "demand while monitoring the sales response."
        )

    # --------------------------------------------------------
    # Strong growth
    # --------------------------------------------------------

    if growth_percent >= 30:

        return (
            "Use a growth-focused promotion or bundle to "
            "capitalize on the strong positive sales trend."
        )

    # --------------------------------------------------------
    # Moderate growth
    # --------------------------------------------------------

    if growth_percent > 10:

        return (
            "Consider a targeted growth promotion to "
            "capitalize on the positive sales trend while "
            "maintaining inventory."
        )

    # --------------------------------------------------------
    # Stable
    # --------------------------------------------------------

    return (
        "Consider a limited promotional campaign only if "
        "additional demand generation is required."
    )


# ============================================================
# BUILD OPPORTUNITY
# ============================================================

def build_promotion_opportunity(
    product: Dict[str, Any],
) -> Dict[str, Any]:

    product_name = product.get(
        "product_name",
        "Unknown Product",
    )

    growth_percent = safe_float(
        product.get("growth_percent")
    )

    stock = safe_int(
        product.get("stock")
    )

    recent_revenue = safe_float(
        product.get("recent_revenue")
    )

    recent_quantity = safe_int(
        product.get("recent_quantity")
    )

    promotion_type = get_promotion_type(
        growth_percent
    )

    # --------------------------------------------------------
    # Out of stock
    # --------------------------------------------------------

    if stock == 0:

        return {
            "product_name": product_name,
            "promotion_type": promotion_type,
            "promotion_score": 0,
            "priority": NOT_RECOMMENDED,
            "growth_percent": growth_percent,
            "stock": stock,
            "recent_revenue": recent_revenue,
            "recent_quantity": recent_quantity,
            "reason": (
                "The product is currently out of stock "
                "and should not be promoted until it is "
                "restocked."
            ),
            "recommended_action": (
                "Restock the product before considering "
                "promotion."
            ),
        }

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    score = calculate_promotion_score(
        growth_percent=growth_percent,
        stock=stock,
        recent_revenue=recent_revenue,
        recent_quantity=recent_quantity,
    )

    priority = get_priority(score)

    reason = build_promotion_reason(
        growth_percent=growth_percent,
        stock=stock,
        recent_revenue=recent_revenue,
    )

    action = build_promotion_action(
        growth_percent=growth_percent,
        stock=stock,
    )

    return {
        "product_name": product_name,
        "promotion_type": promotion_type,
        "promotion_score": score,
        "priority": priority,
        "growth_percent": growth_percent,
        "stock": stock,
        "recent_revenue": recent_revenue,
        "recent_quantity": recent_quantity,
        "reason": reason,
        "recommended_action": action,
    }


# ============================================================
# ALL PROMOTION OPPORTUNITIES
# ============================================================

def get_promotion_opportunities(
    products: List[Dict[str, Any]],
    limit: int = 5,
) -> List[Dict[str, Any]]:

    opportunities = []

    for product in products:

        opportunity = build_promotion_opportunity(
            product
        )

        if (
            opportunity["priority"]
            != NOT_RECOMMENDED
        ):

            opportunities.append(
                opportunity
            )

    # --------------------------------------------------------
    # Sort:
    # 1. Priority
    # 2. Promotion score
    # 3. Revenue
    # --------------------------------------------------------

    priority_rank = {
        HIGH: 3,
        MEDIUM: 2,
        LOW: 1,
        NOT_RECOMMENDED: 0,
    }

    opportunities.sort(
        key=lambda x: (
            priority_rank.get(
                x["priority"],
                0,
            ),
            x["promotion_score"],
            x["recent_revenue"],
        ),
        reverse=True,
    )

    return opportunities[:limit]


# ============================================================
# RECOVERY OPPORTUNITIES
# ============================================================

def get_declining_promotion_opportunities(
    products: List[Dict[str, Any]],
    limit: int = 5,
) -> List[Dict[str, Any]]:

    declining = []

    for product in products:

        growth = safe_float(
            product.get("growth_percent")
        )

        if growth >= 0:
            continue

        opportunity = build_promotion_opportunity(
            product
        )

        if (
            opportunity["priority"]
            != NOT_RECOMMENDED
        ):

            declining.append(
                opportunity
            )

    # Worst decline first, then revenue
    declining.sort(
        key=lambda x: (
            x["growth_percent"],
            -x["recent_revenue"],
        )
    )

    return declining[:limit]


# ============================================================
# GROWTH OPPORTUNITIES
# ============================================================

def get_growing_promotion_opportunities(
    products: List[Dict[str, Any]],
    limit: int = 5,
) -> List[Dict[str, Any]]:

    growing = []

    for product in products:

        growth = safe_float(
            product.get("growth_percent")
        )

        if growth <= 10:
            continue

        opportunity = build_promotion_opportunity(
            product
        )

        if (
            opportunity["priority"]
            != NOT_RECOMMENDED
        ):

            growing.append(
                opportunity
            )

    # Revenue first, then growth
    growing.sort(
        key=lambda x: (
            x["recent_revenue"],
            x["growth_percent"],
            x["promotion_score"],
        ),
        reverse=True,
    )

    return growing[:limit]


# ============================================================
# PROMOTION SUMMARY
# ============================================================

def generate_promotion_summary(
    products: List[Dict[str, Any]],
    limit: int = 5,
) -> Dict[str, Any]:

    all_opportunities = get_promotion_opportunities(
        products=products,
        limit=limit,
    )

    recovery = get_declining_promotion_opportunities(
        products=products,
        limit=limit,
    )

    growth = get_growing_promotion_opportunities(
        products=products,
        limit=limit,
    )

    high_priority = [
        item
        for item in all_opportunities
        if item["priority"] == HIGH
    ]

    medium_priority = [
        item
        for item in all_opportunities
        if item["priority"] == MEDIUM
    ]

    return {
        "total_opportunities": len(
            all_opportunities
        ),

        "recovery_opportunities": len(
            recovery
        ),

        "growth_opportunities": len(
            growth
        ),

        "high_priority_count": len(
            high_priority
        ),

        "medium_priority_count": len(
            medium_priority
        ),

        "top_opportunities": all_opportunities,

        "high_priority": high_priority,

        "medium_priority": medium_priority,

        "recovery_promotions": recovery,

        "growth_promotions": growth,
    }