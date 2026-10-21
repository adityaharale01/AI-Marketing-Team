import json
import re
from typing import Any, Dict, List, Optional

from app.services.ollama_service import generate_response


# ============================================================
# INTENT NAMES
# ============================================================

PROFIT = "PROFIT"
OUT_OF_STOCK = "OUT_OF_STOCK"
LOW_STOCK = "LOW_STOCK"

DECLINING_PRODUCTS = "DECLINING_PRODUCTS"
INCREASING_PRODUCTS = "INCREASING_PRODUCTS"

NEEDS_ATTENTION = "NEEDS_ATTENTION"
FOCUS_PRODUCTS = "FOCUS_PRODUCTS"

RECOMMENDATION = "RECOMMENDATION"
PROMOTION_RECOMMENDATION = "PROMOTION_RECOMMENDATION"

PRODUCT_RANKING = "PRODUCT_RANKING"

SALES_SUMMARY = "SALES_SUMMARY"
REVENUE_SUMMARY = "REVENUE_SUMMARY"

SPECIFIC_PRODUCT = "SPECIFIC_PRODUCT"


# ============================================================
# CREATE INTENT
# ============================================================

def create_intent(
    intent: str,
    metric: Optional[str] = None,
    direction: Optional[str] = None,
    limit: Optional[int] = None,
    product_name: Optional[str] = None,
) -> Dict[str, Any]:

    return {
        "intent": intent,
        "metric": metric,
        "direction": direction,
        "limit": limit,
        "product_name": product_name,
    }


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text: str) -> str:

    if not text:
        return ""

    text = text.lower().strip()

    text = re.sub(r"[^\w\s%.-]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text


# ============================================================
# LIMIT DETECTION
# ============================================================

def detect_limit(query: str) -> Optional[int]:

    q = normalize_text(query)

    match = re.search(r"\btop\s+(\d+)\b", q)

    if match:
        return int(match.group(1))

    match = re.search(r"\b(\d+)\s+products?\b", q)

    if match:
        return int(match.group(1))

    singular_words = [
        "which product",
        "which one",
        "what product",
        "best product",
        "worst product",
        "top product",
    ]

    for word in singular_words:
        if word in q:
            return 1

    multiple_words = [
        "which products",
        "what products",
        "products",
        "top",
        "best products",
        "worst products",
        "all products",
    ]

    for word in multiple_words:
        if word in q:
            return 5

    return None


# ============================================================
# PRODUCT NAME EXTRACTION
# ============================================================

def extract_product_name(query: str) -> Optional[str]:

    q = normalize_text(query)

    patterns = [
        r"about\s+(.+?)(?:\s+in\s+the\s+last|\s+for\s+the\s+last|\s+last\s+\d+|\s*$)",
        r"for\s+product\s+(.+?)(?:\s+in\s+the\s+last|\s+for\s+the\s+last|\s*$)",
        r"product\s+(.+?)(?:\s+in\s+the\s+last|\s+for\s+the\s+last|\s*$)",
    ]

    for pattern in patterns:

        match = re.search(pattern, q)

        if match:

            value = match.group(1).strip()

            if value:
                return value

    return None


# ============================================================
# PRODUCT RANKING
# ============================================================

def detect_product_ranking(
    query: str,
) -> Optional[Dict[str, Any]]:

    q = normalize_text(query)

    limit = detect_limit(q)

    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    revenue_words = [
        "highest revenue",
        "best revenue",
        "most revenue",
        "highest earning",
        "highest earnings",
        "earning the most",
        "earns the most",
        "makes the most money",
        "made the most money",
        "most money",
        "best selling by revenue",
        "top revenue",
        "generated most revenue",
        "generated the most revenue",
    ]

    for word in revenue_words:

        if word in q:

            return create_intent(
                PRODUCT_RANKING,
                metric="revenue",
                direction="highest",
                limit=limit or 1,
            )

    # --------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------

    quantity_words = [
        "sold the most",
        "sell the most",
        "selling the most",
        "most units",
        "highest quantity",
        "highest sales volume",
        "most sold",
        "best selling product",
        "best selling products",
        "selling most",
        "sold most",
    ]

    for word in quantity_words:

        if word in q:

            return create_intent(
                PRODUCT_RANKING,
                metric="quantity",
                direction="highest",
                limit=limit or 1,
            )

    # --------------------------------------------------------
    # HIGHEST GROWTH
    # --------------------------------------------------------

    highest_growth_words = [
        "highest growth",
        "highest growing",
        "growing fastest",
        "fastest growing",
        "growth the most",
        "increased the most",
        "increasing the most",
        "best growth",
    ]

    for word in highest_growth_words:

        if word in q:

            return create_intent(
                PRODUCT_RANKING,
                metric="growth",
                direction="highest",
                limit=limit or 1,
            )

    # --------------------------------------------------------
    # LOWEST GROWTH
    # --------------------------------------------------------

    lowest_growth_words = [
        "lowest growth",
        "worst growth",
        "declining the most",
        "declined the most",
        "decreased the most",
        "worst performing",
        "worst performance",
        "performing the worst",
    ]

    for word in lowest_growth_words:

        if word in q:

            return create_intent(
                PRODUCT_RANKING,
                metric="growth",
                direction="lowest",
                limit=limit or 1,
            )

    return None


# ============================================================
# FALLBACK CLASSIFIER
# ============================================================

def fallback_classify_query(
    query: str,
) -> List[Dict[str, Any]]:

    q = normalize_text(query)

    intents: List[Dict[str, Any]] = []

    # ========================================================
    # PROMOTION DETECTION FIRST
    # ========================================================

    promotion_words = [
        "promote",
        "promotion",
        "promotional",
        "promotions",
        "advertise",
        "advertising",
        "campaign",
        "marketing",
        "promotion opportunity",
        "promotion opportunities",
        "promotion candidate",
        "promotion candidates",
        "best candidates for promotion",
        "candidates for promotion",
    ]

    has_promotion = any(
        word in q for word in promotion_words
    )

    # ========================================================
    # PRODUCT RANKING
    # ========================================================

    ranking_intent = detect_product_ranking(q)

    if ranking_intent and not has_promotion:
        intents.append(ranking_intent)

    # ========================================================
    # PROFIT
    # ========================================================

    profit_words = [
        "profit",
        "profitable",
        "profit margin",
        "profitability",
    ]

    if any(word in q for word in profit_words):

        intents.append(
            create_intent(
                PROFIT,
                metric="profit",
            )
        )

    # ========================================================
    # OUT OF STOCK
    # ========================================================

    out_of_stock_words = [
        "out of stock",
        "out-of-stock",
        "stock is 0",
        "stock 0",
        "no stock",
        "zero stock",
        "sold out",
    ]

    if any(word in q for word in out_of_stock_words):

        intents.append(
            create_intent(
                OUT_OF_STOCK,
                metric="stock",
                direction="zero",
                limit=5,
            )
        )

    # ========================================================
    # LOW STOCK
    # ========================================================

    low_stock_words = [
        "low stock",
        "running low",
        "almost out of stock",
        "low inventory",
        "inventory is low",
    ]

    if any(word in q for word in low_stock_words):

        intents.append(
            create_intent(
                LOW_STOCK,
                metric="stock",
                direction="low",
                limit=5,
            )
        )

    # ========================================================
    # DECLINING PRODUCTS
    # ========================================================

    declining_words = [
        "declining",
        "decline",
        "declined",
        "decreasing",
        "decrease",
        "falling",
        "fall",
        "dropping",
        "drop",
        "negative growth",
        "poor growth",
        "losing sales",
        "sales are down",
        "sales decreased",
        "underperforming",
        "under performing",
    ]

    has_declining = any(
        word in q for word in declining_words
    )

    if has_declining:

        intents.append(
            create_intent(
                DECLINING_PRODUCTS,
                metric="growth",
                direction="negative",
            )
        )

    # ========================================================
    # INCREASING PRODUCTS
    # ========================================================

    increasing_words = [
        "increasing",
        "increase",
        "increased",
        "growing",
        "growth",
        "rising",
        "rise",
        "improving",
        "improved",
        "performing well",
        "doing well",
        "best performing",
    ]

    has_increasing = any(
        word in q for word in increasing_words
    )

    # Do not interpret "promotion opportunity" as growth
    if has_increasing and not has_promotion:

        intents.append(
            create_intent(
                INCREASING_PRODUCTS,
                metric="growth",
                direction="positive",
            )
        )

    # ========================================================
    # NEEDS ATTENTION
    # ========================================================

    attention_words = [
        "needs attention",
        "need attention",
        "require attention",
        "requires attention",
        "problem products",
        "problematic products",
        "poor performing",
        "poorly performing",
    ]

    if any(word in q for word in attention_words):

        intents.append(
            create_intent(
                NEEDS_ATTENTION,
                metric="growth",
                direction="negative",
                limit=5,
            )
        )

    # ========================================================
    # PROMOTION RECOMMENDATION
    # ========================================================

    if has_promotion:

        intents.append(
            create_intent(
                PROMOTION_RECOMMENDATION,
                metric="growth",
                direction="positive",
                limit=detect_limit(q) or 5,
            )
        )

    # ========================================================
    # GENERIC RECOMMENDATION
    # ========================================================

    recommendation_words = [
        "what should i do",
        "what can i do",
        "what do you recommend",
        "what should we do",
        "how should i improve",
        "how can i improve",
        "recommendation",
        "recommend",
        "suggest",
        "suggestion",
        "what action",
        "next step",
        "next steps",
    ]

    has_recommendation = any(
        word in q for word in recommendation_words
    )

    # Promotion should NOT become generic recommendation
    if has_recommendation and not has_promotion:

        intents.append(
            create_intent(
                RECOMMENDATION,
                metric="general",
            )
        )

    # ========================================================
    # FOCUS PRODUCTS
    # ========================================================

    focus_words = [
        "focus products",
        "products should i focus",
        "which products should i focus",
        "what products should i focus",
        "products to focus on",
        "focus on",
    ]

    if any(word in q for word in focus_words):

        intents.append(
            create_intent(
                FOCUS_PRODUCTS,
                metric="growth",
                direction="positive",
                limit=3,
            )
        )

    # ========================================================
    # SALES SUMMARY
    # ========================================================

    sales_summary_words = [
        "sales summary",
        "sales performance",
        "overall sales",
        "total sales",
        "how are sales",
        "how did sales",
        "sales doing",
    ]

    if any(word in q for word in sales_summary_words):

        intents.append(
            create_intent(
                SALES_SUMMARY,
                metric="quantity",
            )
        )

    # ========================================================
    # REVENUE SUMMARY
    # ========================================================

    revenue_summary_words = [
        "revenue summary",
        "revenue performance",
        "overall revenue",
        "total revenue",
        "how is revenue",
        "how did revenue",
        "revenue doing",
    ]

    if any(word in q for word in revenue_summary_words):

        intents.append(
            create_intent(
                REVENUE_SUMMARY,
                metric="revenue",
            )
        )

    # ========================================================
    # SPECIFIC PRODUCT
    # ========================================================

    product_name = extract_product_name(query)

    if product_name:

        intents.append(
            create_intent(
                SPECIFIC_PRODUCT,
                product_name=product_name,
            )
        )

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique_intents = []

    seen = set()

    for intent in intents:

        key = (
            intent.get("intent"),
            intent.get("metric"),
            intent.get("direction"),
            intent.get("product_name"),
        )

        if key not in seen:

            seen.add(key)

            unique_intents.append(intent)

    return unique_intents


# ============================================================
# INTENT NORMALIZATION FROM LLM
# ============================================================

def normalize_llm_intents(
    intents: Any,
) -> List[Dict[str, Any]]:

    if not isinstance(intents, list):
        return []

    valid_intents = {
        PROFIT,
        OUT_OF_STOCK,
        LOW_STOCK,
        DECLINING_PRODUCTS,
        INCREASING_PRODUCTS,
        NEEDS_ATTENTION,
        FOCUS_PRODUCTS,
        RECOMMENDATION,
        PROMOTION_RECOMMENDATION,
        PRODUCT_RANKING,
        SALES_SUMMARY,
        REVENUE_SUMMARY,
        SPECIFIC_PRODUCT,
    }

    normalized = []

    for item in intents:

        if not isinstance(item, dict):
            continue

        intent_name = item.get("intent")

        if not isinstance(intent_name, str):
            continue

        intent_name = intent_name.upper().strip()

        if intent_name not in valid_intents:
            continue

        limit = item.get("limit")

        if isinstance(limit, str):

            try:
                limit = int(limit)
            except ValueError:
                limit = None

        if limit is not None:

            try:
                limit = int(limit)
            except (TypeError, ValueError):
                limit = None

        normalized.append(
            create_intent(
                intent=intent_name,
                metric=item.get("metric"),
                direction=item.get("direction"),
                limit=limit,
                product_name=item.get("product_name"),
            )
        )

    return normalized


# ============================================================
# BUILD LLM PROMPT
# ============================================================

def build_intent_prompt(query: str) -> str:

    return f"""
You are an intent classifier for a business analytics system.

Classify the user's query into one or more intents.

Allowed intents:

PROFIT
OUT_OF_STOCK
LOW_STOCK
DECLINING_PRODUCTS
INCREASING_PRODUCTS
NEEDS_ATTENTION
FOCUS_PRODUCTS
RECOMMENDATION
PROMOTION_RECOMMENDATION
PRODUCT_RANKING
SALES_SUMMARY
REVENUE_SUMMARY
SPECIFIC_PRODUCT

Important rules:

1. If the user asks which products to promote, use PROMOTION_RECOMMENDATION.

2. If the user asks for promotion opportunities, use PROMOTION_RECOMMENDATION.

3. If the user asks for candidates for promotion, use PROMOTION_RECOMMENDATION.

4. If the user asks about declining products AND asks whether to promote them, return:
DECLINING_PRODUCTS + PROMOTION_RECOMMENDATION.

5. If the user asks about increasing products AND asks whether to promote them, return:
INCREASING_PRODUCTS + PROMOTION_RECOMMENDATION.

6. Words such as promote, promotion, promotional, advertise, advertising,
campaign, marketing, promotion opportunity, promotion opportunities,
promotion candidates should strongly indicate PROMOTION_RECOMMENDATION.

7. Do NOT classify promotion opportunity questions as PROFIT.

8. "What products have the best promotion opportunity?" means PROMOTION_RECOMMENDATION.

9. "Which products are the best candidates for promotion?" means PROMOTION_RECOMMENDATION.

10. "Which products have the best promotion opportunities?" means PROMOTION_RECOMMENDATION.

11. "Which declining products should I promote?" means:
DECLINING_PRODUCTS + PROMOTION_RECOMMENDATION.

12. "Which increasing products should I promote?" means:
INCREASING_PRODUCTS + PROMOTION_RECOMMENDATION.

13. "Which products are declining?" means DECLINING_PRODUCTS.

14. "Which products are increasing?" means INCREASING_PRODUCTS.

15. "Which product sold the most?" means PRODUCT_RANKING with metric quantity.

16. "Which product generated the most revenue?" means PRODUCT_RANKING with metric revenue.

17. "Which product has the highest growth?" means PRODUCT_RANKING with metric growth.

18. "Which product has the lowest growth?" means PRODUCT_RANKING with metric growth and direction lowest.

19. "What is the sales summary?" means SALES_SUMMARY.

20. "What is the revenue summary?" means REVENUE_SUMMARY.

21. "Which products need attention?" means NEEDS_ATTENTION.

22. "Which products should I focus on?" means FOCUS_PRODUCTS.

23. Use multiple intents when the query clearly asks for multiple things.

Return ONLY valid JSON.

Format:

{{
    "intents": [
        {{
            "intent": "INTENT_NAME",
            "metric": "growth",
            "direction": "positive",
            "limit": 5,
            "product_name": null
        }}
    ]
}}

User query:

{query}
"""


# ============================================================
# CLEAN LLM JSON
# ============================================================

def clean_json_response(response: str) -> str:

    if not response:
        return ""

    response = response.strip()

    if "```json" in response:

        response = response.replace("```json", "")
        response = response.replace("```", "")

    elif "```" in response:

        response = response.replace("```", "")

    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end != -1:

        response = response[start:end + 1]

    return response.strip()


# ============================================================
# LLM CLASSIFIER
# ============================================================

async def classify_with_llm(
    query: str,
) -> List[Dict[str, Any]]:

    try:

        prompt = build_intent_prompt(query)

        response = await generate_response(prompt)

        cleaned = clean_json_response(response)

        if not cleaned:
            return []

        data = json.loads(cleaned)

        if isinstance(data, dict):

            intents = data.get("intents", [])

        else:

            intents = []

        return normalize_llm_intents(intents)

    except Exception as e:

        print(
            f"[Intent Classifier] LLM classification failed: {e}"
        )

        return []


# ============================================================
# MERGE INTENTS
# ============================================================

def merge_intents(
    llm_intents: List[Dict[str, Any]],
    fallback_intents: List[Dict[str, Any]],
    query: str,
) -> List[Dict[str, Any]]:

    q = normalize_text(query)

    merged = []

    # --------------------------------------------------------
    # First add LLM intents
    # --------------------------------------------------------

    for intent in llm_intents:

        if intent not in merged:
            merged.append(intent)

    # --------------------------------------------------------
    # Add fallback intents when important
    # --------------------------------------------------------

    explicit_promotion_words = [
        "promote",
        "promotion",
        "promotional",
        "promotions",
        "advertise",
        "advertising",
        "campaign",
        "marketing",
        "promotion opportunity",
        "promotion opportunities",
        "promotion candidate",
        "promotion candidates",
        "best candidates for promotion",
        "candidates for promotion",
    ]

    has_promotion = any(
        word in q for word in explicit_promotion_words
    )

    if has_promotion:

        has_promotion_intent = any(
            item.get("intent") == PROMOTION_RECOMMENDATION
            for item in merged
        )

        if not has_promotion_intent:

            merged.append(
                create_intent(
                    PROMOTION_RECOMMENDATION,
                    metric="growth",
                    direction="positive",
                    limit=detect_limit(q) or 5,
                )
            )

    # --------------------------------------------------------
    # Explicit declining + promotion
    # --------------------------------------------------------

    if has_promotion and any(
        word in q
        for word in [
            "declining",
            "decline",
            "declined",
            "decreasing",
            "decrease",
            "falling",
            "dropping",
        ]
    ):

        if not any(
            item.get("intent") == DECLINING_PRODUCTS
            for item in merged
        ):

            merged.append(
                create_intent(
                    DECLINING_PRODUCTS,
                    metric="growth",
                    direction="negative",
                )
            )

    # --------------------------------------------------------
    # Explicit increasing + promotion
    # --------------------------------------------------------

    if has_promotion and any(
        word in q
        for word in [
            "increasing",
            "increase",
            "increased",
            "growing",
            "rising",
            "improving",
        ]
    ):

        if not any(
            item.get("intent") == INCREASING_PRODUCTS
            for item in merged
        ):

            merged.append(
                create_intent(
                    INCREASING_PRODUCTS,
                    metric="growth",
                    direction="positive",
                )
            )

    # --------------------------------------------------------
    # Fallback safety
    # --------------------------------------------------------

    for fallback in fallback_intents:

        fallback_name = fallback.get("intent")

        # Promotion must always be preserved
        if fallback_name == PROMOTION_RECOMMENDATION:

            if not any(
                item.get("intent") == PROMOTION_RECOMMENDATION
                for item in merged
            ):

                merged.append(fallback)

            continue

        # Preserve important explicit intents
        if fallback_name in {
            DECLINING_PRODUCTS,
            INCREASING_PRODUCTS,
            OUT_OF_STOCK,
            LOW_STOCK,
            NEEDS_ATTENTION,
            FOCUS_PRODUCTS,
            PRODUCT_RANKING,
            SALES_SUMMARY,
            REVENUE_SUMMARY,
            SPECIFIC_PRODUCT,
        }:

            if not any(
                item.get("intent") == fallback_name
                for item in merged
            ):

                merged.append(fallback)

    # --------------------------------------------------------
    # CRITICAL SAFETY:
    # Promotion queries should NEVER become only PROFIT
    # --------------------------------------------------------

    if has_promotion:

        merged = [
            item
            for item in merged
            if item.get("intent") != PROFIT
        ]

        if not any(
            item.get("intent") == PROMOTION_RECOMMENDATION
            for item in merged
        ):

            merged.insert(
                0,
                create_intent(
                    PROMOTION_RECOMMENDATION,
                    metric="growth",
                    direction="positive",
                    limit=detect_limit(q) or 5,
                ),
            )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    final_intents = []

    seen = set()

    for item in merged:

        key = (
            item.get("intent"),
            item.get("metric"),
            item.get("direction"),
            item.get("product_name"),
        )

        if key not in seen:

            seen.add(key)

            final_intents.append(item)

    return final_intents


# ============================================================
# MAIN ASYNC CLASSIFIER
# ============================================================

async def classify_query(
    query: str,
) -> List[Dict[str, Any]]:

    if not query or not query.strip():

        return []

    # Always run deterministic fallback
    fallback_intents = fallback_classify_query(query)

    # Run LLM classifier
    llm_intents = await classify_with_llm(query)

    # Merge both
    final_intents = merge_intents(
        llm_intents=llm_intents,
        fallback_intents=fallback_intents,
        query=query,
    )

    return final_intents


# ============================================================
# SYNCHRONOUS CLASSIFIER
# ============================================================

def classify_query_sync(
    query: str,
) -> List[Dict[str, Any]]:

    return fallback_classify_query(query)