from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.product import Product
from app.models.sale import Sale


def get_sales_summary(
    db: Session,
    business_id: int,
    period_days: int = 30
):
    """
    Generate an aggregated sales summary for a business.

    PostgreSQL is the source of truth.
    This summary will later be indexed into ChromaDB
    for RAG.
    """

    # =========================================================
    # 1. FIND BUSINESS
    # =========================================================

    business = (
        db.query(Business)
        .filter(
            Business.id == business_id
        )
        .first()
    )

    if not business:
        raise ValueError("Business not found")

    # =========================================================
    # 2. FIND LATEST SALE
    # =========================================================

    latest_sale = (
        db.query(Sale.sale_date)
        .filter(
            Sale.business_id == business_id
        )
        .order_by(
            Sale.sale_date.desc()
        )
        .first()
    )

    if not latest_sale:
        return {
            "business_id": business_id,
            "business_name": business.business_name,
            "message": "No sales data available."
        }

    latest_date = latest_sale[0]

    # =========================================================
    # 3. CREATE TWO TIME PERIODS
    # =========================================================

    recent_start = (
        latest_date -
        timedelta(days=period_days)
    )

    previous_start = (
        latest_date -
        timedelta(days=period_days * 2)
    )

    # =========================================================
    # 4. GET SALES FOR BOTH PERIODS
    # =========================================================

    sales = (
        db.query(Sale)
        .filter(
            Sale.business_id == business_id,
            Sale.sale_date > previous_start,
            Sale.sale_date <= latest_date
        )
        .all()
    )

    recent_sales = [
        sale
        for sale in sales
        if sale.sale_date > recent_start
    ]

    previous_sales = [
        sale
        for sale in sales
        if sale.sale_date <= recent_start
    ]

    # =========================================================
    # 5. OVERALL QUANTITY
    # =========================================================

    recent_quantity = sum(
        sale.quantity
        for sale in recent_sales
    )

    previous_quantity = sum(
        sale.quantity
        for sale in previous_sales
    )

    # =========================================================
    # 6. OVERALL REVENUE
    # =========================================================

    recent_revenue = sum(
        (
            sale.total_amount
            if sale.total_amount is not None
            else Decimal("0")
        )
        for sale in recent_sales
    )

    previous_revenue = sum(
        (
            sale.total_amount
            if sale.total_amount is not None
            else Decimal("0")
        )
        for sale in previous_sales
    )

    # =========================================================
    # 7. QUANTITY GROWTH
    # =========================================================

    if previous_quantity > 0:

        quantity_growth = (
            (
                recent_quantity -
                previous_quantity
            )
            / previous_quantity
        ) * 100

    else:
        quantity_growth = None

    # =========================================================
    # 8. REVENUE GROWTH
    # =========================================================

    if previous_revenue > 0:

        revenue_growth = (
            (
                float(recent_revenue) -
                float(previous_revenue)
            )
            / float(previous_revenue)
        ) * 100

    else:
        revenue_growth = None

    # =========================================================
    # 9. GET PRODUCTS
    # =========================================================

    products = (
        db.query(Product)
        .filter(
            Product.business_id == business_id
        )
        .all()
    )

    product_summary = []

    # =========================================================
    # 10. PRODUCT ANALYSIS
    # =========================================================

    for product in products:

        product_recent_sales = [
            sale
            for sale in recent_sales
            if sale.product_id == product.id
        ]

        product_previous_sales = [
            sale
            for sale in previous_sales
            if sale.product_id == product.id
        ]

        # -----------------------------------------------------
        # Recent quantity
        # -----------------------------------------------------

        recent_product_quantity = sum(
            sale.quantity
            for sale in product_recent_sales
        )

        # -----------------------------------------------------
        # Previous quantity
        # -----------------------------------------------------

        previous_product_quantity = sum(
            sale.quantity
            for sale in product_previous_sales
        )

        # -----------------------------------------------------
        # Recent revenue
        # -----------------------------------------------------

        recent_product_revenue = sum(
            (
                sale.total_amount
                if sale.total_amount is not None
                else Decimal("0")
            )
            for sale in product_recent_sales
        )

        # -----------------------------------------------------
        # Previous revenue
        # -----------------------------------------------------

        previous_product_revenue = sum(
            (
                sale.total_amount
                if sale.total_amount is not None
                else Decimal("0")
            )
            for sale in product_previous_sales
        )

        # -----------------------------------------------------
        # Product growth
        # -----------------------------------------------------

        if previous_product_quantity > 0:

            growth = (
                (
                    recent_product_quantity -
                    previous_product_quantity
                )
                / previous_product_quantity
            ) * 100

        else:
            growth = None

        # -----------------------------------------------------
        # Product status
        # -----------------------------------------------------

        if (
            previous_product_quantity == 0
            and recent_product_quantity > 0
        ):

            status = "New Sales"

        elif (
            growth is not None
            and growth > 10
        ):

            status = "Increasing"

        elif (
            growth is not None
            and growth < -10
        ):

            status = "Declining"

        else:

            status = "Stable"

        # -----------------------------------------------------
        # Add product
        # -----------------------------------------------------

        product_summary.append({

            "product_id": product.id,

            "product_name": product.product_name,

            "category": product.category,

            "recent_quantity": (
                recent_product_quantity
            ),

            "previous_quantity": (
                previous_product_quantity
            ),

            "recent_revenue": float(
                recent_product_revenue
            ),

            "previous_revenue": float(
                previous_product_revenue
            ),

            "growth_percent": (
                round(growth, 2)
                if growth is not None
                else None
            ),

            "stock": product.stock,

            "status": status
        })

    # =========================================================
    # 11. SORT PRODUCTS BY REVENUE
    # =========================================================

    top_products = sorted(
        product_summary,
        key=lambda product:
            product["recent_revenue"],
        reverse=True
    )

    # =========================================================
    # 12. INCREASING PRODUCTS
    # =========================================================

    increasing_products = [
        product
        for product in product_summary
        if product["status"] in [
            "Increasing",
            "New Sales"
        ]
    ]

    # =========================================================
    # 13. DECLINING PRODUCTS
    # =========================================================

    declining_products = [
        product
        for product in product_summary
        if product["status"] == "Declining"
    ]

    # =========================================================
    # 14. LOW STOCK PRODUCTS
    # =========================================================

    low_stock_products = [

        {
            "product_id": product.id,
            "product_name": product.product_name,
            "stock": product.stock
        }

        for product in products

        if product.stock <= 10
    ]

    # =========================================================
    # 15. RETURN VERIFIED SUMMARY
    # =========================================================

    return {

        "business_id": business_id,

        "business_name": business.business_name,

        "business_type": business.business_type,

        "latest_sale_date": latest_date,

        "period_days": period_days,

        "recent_period": {

            "quantity_sold":
                recent_quantity,

            "revenue":
                float(recent_revenue)
        },

        "previous_period": {

            "quantity_sold":
                previous_quantity,

            "revenue":
                float(previous_revenue)
        },

        "growth": {

            "quantity_percent": (
                round(quantity_growth, 2)
                if quantity_growth is not None
                else None
            ),

            "revenue_percent": (
                round(revenue_growth, 2)
                if revenue_growth is not None
                else None
            )
        },

        "top_products":
            top_products[:10],

        "increasing_products":
            increasing_products,

        "declining_products":
            declining_products,

        "low_stock_products":
            low_stock_products
    }