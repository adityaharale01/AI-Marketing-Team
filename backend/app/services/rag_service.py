import chromadb

from sentence_transformers import SentenceTransformer

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.product import Product
from app.models.sale import Sale
from app.models.campaign import Campaign

from app.services.business_analytics_service import (
    get_business_analytics
)

from app.services.sales_summary_service import (
    get_sales_summary
)
# =========================================================
# 1. EMBEDDING MODEL
# =========================================================

embedding_model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)


# =========================================================
# 2. CHROMADB CLIENT
# =========================================================

chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)


# =========================================================
# 3. CHROMADB COLLECTION
# =========================================================

collection = chroma_client.get_or_create_collection(
    name="business_knowledge"
)


# =========================================================
# 4. ADD / UPDATE CONTEXT
# =========================================================

def add_context(
    context: str,
    context_id: str,
    business_id: int = None,
    context_type: str = "general"
):
    """
    Add business information to ChromaDB.

    Each document stores:
    - business_id
    - context_type

    This allows us to retrieve information belonging
    only to a particular business.
    """

    # Generate embedding
    embedding = embedding_model.encode(
        context
    ).tolist()

    # Metadata
    metadata = {
        "business_id": (
            str(business_id)
            if business_id is not None
            else "unknown"
        ),
        "context_type": context_type
    }

    # Insert/update document
    collection.upsert(
        ids=[context_id],
        documents=[context],
        embeddings=[embedding],
        metadatas=[metadata]
    )


# =========================================================
# 5. GENERAL RAG SEARCH
# =========================================================

def search_context(
    query: str,
    n_results: int = 3
):
    """
    Search the complete business knowledge collection.
    """

    query_embedding = embedding_model.encode(
        query
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    return results


# =========================================================
# 6. BUSINESS-SPECIFIC RAG SEARCH
# =========================================================

def search_business_context(
    query: str,
    business_id: int,
    n_results: int = 5,
    context_type: str = None
):
    """
    Search ChromaDB for a specific business.

    If context_type is provided, only documents
    of that type are retrieved.
    """

    query_embedding = embedding_model.encode(
        query
    ).tolist()

    # Always restrict search to the requested business
    where_filter = {
        "business_id": str(business_id)
    }

    # Optional context-type filtering
    if context_type:

        where_filter = {
            "$and": [
                {
                    "business_id": str(business_id)
                },
                {
                    "context_type": context_type
                }
            ]
        }

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter
    )

    return results


# =========================================================
# 7. BUILD TEXT CONTEXT FROM SEARCH RESULTS
# =========================================================

def build_context(results):
    """
    Convert ChromaDB search results into plain text.
    """

    documents = results.get(
        "documents",
        [[]]
    )[0]

    return "\n\n".join(documents)


# =========================================================
# 8. INDEX COMPLETE BUSINESS DATA
# =========================================================

def index_business_data(
    db: Session,
    business_id: int
):
    """
    Index business, product, sales and campaign
    information into ChromaDB.
    """

    # -----------------------------------------------------
    # Find business
    # -----------------------------------------------------

    business = (
        db.query(Business)
        .filter(
            Business.id == business_id
        )
        .first()
    )

    if not business:
        raise ValueError(
            "Business not found"
        )

    # =====================================================
    # BUSINESS INFORMATION
    # =====================================================

    context = f"""
Business Information

Business ID: {business.id}
Business Name: {business.business_name}
Business Type: {business.business_type}
Business Description: {business.description or "Not available"}

Location:
{business.city or ""},
{business.state or ""},
{business.country or ""}

Email: {business.email or "Not available"}
Phone: {business.phone or "Not available"}
Website: {business.website or "Not available"}
"""

    add_context(
        context=context,
        context_id=f"business_{business.id}",
        business_id=business.id,
        context_type="business"
    )

    # =====================================================
    # PRODUCT INFORMATION
    # =====================================================

    for product in business.products:

        product_context = f"""
Product Information

Business ID: {business.id}
Business: {business.business_name}
Business Type: {business.business_type}

Product ID: {product.id}
Product Name: {product.product_name}
Category: {product.category}

Description:
{product.description or "Not available"}

SKU: {product.sku}
Price: ₹{product.price}
Current Stock: {product.stock}

Product Active:
{product.is_active}
"""

        add_context(
            context=product_context,
            context_id=(
                f"business_{business.id}"
                f"_product_{product.id}"
            ),
            business_id=business.id,
            context_type="product"
        )

    # =====================================================
    # SALES INFORMATION
    # =====================================================

    sales = (
        db.query(Sale)
        .filter(
            Sale.business_id == business_id
        )
        .all()
    )

    for sale in sales:

        sale_context = f"""
Sales Record

Business ID: {business.id}
Business: {business.business_name}

Sale ID: {sale.id}
Product ID: {sale.product_id}

Quantity Sold: {sale.quantity}
Unit Price: ₹{sale.unit_price}
Total Amount: ₹{sale.total_amount}

Sale Date: {sale.sale_date}
"""

        add_context(
            context=sale_context,
            context_id=(
                f"business_{business.id}"
                f"_sale_{sale.id}"
            ),
            business_id=business.id,
            context_type="sale"
        )

    # =====================================================
    # CAMPAIGN INFORMATION
    # =====================================================

    campaigns = (
        db.query(Campaign)
        .filter(
            Campaign.business_id == business_id
        )
        .all()
    )

    for campaign in campaigns:

        campaign_context = f"""
Marketing Campaign

Business ID: {business.id}
Business: {business.business_name}

Campaign ID: {campaign.id}
Campaign Name: {campaign.campaign_name}

Objective:
{campaign.objective}

Target Audience:
{campaign.target_audience or "Not specified"}

Platform:
{campaign.platform}

Status:
{campaign.status}

Budget:
{campaign.budget or "Not specified"}
"""

        add_context(
            context=campaign_context,
            context_id=(
                f"business_{business.id}"
                f"_campaign_{campaign.id}"
            ),
            business_id=business.id,
            context_type="campaign"
        )

    # =====================================================
    # RETURN RESULT
    # =====================================================

    return {
        "business_id": business_id,
        "message": "Business data indexed successfully"
    }


# =========================================================
# 9. INDEX PRODUCT PERFORMANCE
# =========================================================

def index_product_performance(
    db: Session,
    business_id: int
):
    """
    Index the latest verified product performance
    calculated directly from PostgreSQL.
    """

    analytics = get_business_analytics(
        db=db,
        business_id=business_id,
        period_days=7
    )

    business_name = analytics["business_name"]

    for product in analytics.get("products", []):

        context = f"""
Verified Product Performance

Business ID: {business_id}
Business: {business_name}

Product ID: {product["product_id"]}
Product: {product["product_name"]}
Category: {product["category"]}

Recent Sales:
{product["recent_quantity"]} units

Previous Period Sales:
{product["previous_quantity"]} units

Sales Growth:
{product["growth_percent"]}%

Recent Revenue:
₹{product["recent_revenue"]}

Current Stock:
{product["stock"]}

Performance Status:
{product["status"]}

Performance Label:
{product["performance_label"]}

This performance information is calculated
from actual sales records stored in PostgreSQL.
"""

        add_context(
            context=context,
            context_id=(
                f"business_{business_id}"
                f"_performance_product_"
                f"{product['product_id']}"
            ),
            business_id=business_id,
            context_type="performance"
        )

    return analytics

def index_sales_summary(
    db: Session,
    business_id: int
):

    summary = get_sales_summary(
        db=db,
        business_id=business_id,
        period_days=30
    )

    if "message" in summary:
        return summary

    business_name = summary["business_name"]

    context = f"""
Verified Business Sales Summary

Business ID: {business_id}
Business: {business_name}
Business Type: {summary["business_type"]}

Analysis Period:
{summary["period_days"]} days

Recent Quantity Sold:
{summary["recent_period"]["quantity_sold"]}

Previous Quantity Sold:
{summary["previous_period"]["quantity_sold"]}

Recent Revenue:
₹{summary["recent_period"]["revenue"]}

Previous Revenue:
₹{summary["previous_period"]["revenue"]}

Quantity Growth:
{summary["growth"]["quantity_percent"]}%

Revenue Growth:
{summary["growth"]["revenue_percent"]}%

TOP PRODUCTS BY RECENT REVENUE:

{summary["top_products"]}

INCREASING PRODUCTS:

{summary["increasing_products"]}

DECLINING PRODUCTS:

{summary["declining_products"]}

LOW STOCK PRODUCTS:

{summary["low_stock_products"]}

This information is calculated directly
from actual PostgreSQL sales and product data.
"""

    add_context(
        context=context,
        context_id=(
            f"business_{business_id}_sales_summary"
        ),
        business_id=business_id,
        context_type="sales_summary"
    )

    return summary