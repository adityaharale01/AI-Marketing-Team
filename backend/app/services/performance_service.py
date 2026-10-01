from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.product import Product
from app.models.sale import Sale


def get_product_performance(
    db: Session,
    business_id: int,
    period_days: int = 7
):
    """
    Calculate actual product performance from PostgreSQL sales data.

    Recent period:
        latest sale date -> previous period_days

    Previous period:
        previous period_days before recent period
    """

    business = (
        db.query(Business)
        .filter(Business.id == business_id)
        .first()
    )

    if not business:
        raise ValueError("Business not found")

    latest_sale = (
        db.query(Sale.sale_date)
        .filter(Sale.business_id == business_id)
        .order_by(Sale.sale_date.desc())
        .first()
    )

    if not latest_sale:
        return {
            "business_id": business_id,
            "business_name": business.business_name,
            "period_days": period_days,
            "products": []
        }

    latest_date = latest_sale[0]

    recent_start = latest_date - timedelta(days=period_days)

    previous_start = latest_date - timedelta(days=period_days * 2)

    products = (
        db.query(Product)
        .filter(
            Product.business_id == business_id,
            
        )
        .all()
    )

    performance = []

    for product in products:

        recent_sales = (
            db.query(Sale)
            .filter(
                Sale.business_id == business_id,
                Sale.product_id == product.id,
                Sale.sale_date > recent_start,
                Sale.sale_date <= latest_date
            )
            .all()
        )

        previous_sales = (
            db.query(Sale)
            .filter(
                Sale.business_id == business_id,
                Sale.product_id == product.id,
                Sale.sale_date > previous_start,
                Sale.sale_date <= recent_start
            )
            .all()
        )

        recent_quantity = sum(
            sale.quantity
            for sale in recent_sales
        )

        previous_quantity = sum(
            sale.quantity
            for sale in previous_sales
        )

        recent_revenue = sum(
            (sale.total_amount or Decimal("0"))
            for sale in recent_sales
        )

        previous_revenue = sum(
            (sale.total_amount or Decimal("0"))
            for sale in previous_sales
        )

        if previous_quantity > 0:
            quantity_growth = (
            (recent_quantity - previous_quantity)
            / previous_quantity
                    ) * 100
        else:
                quantity_growth = None

        if previous_revenue > 0:
            revenue_growth = (
        (float(recent_revenue) - float(previous_revenue))
        / float(previous_revenue)
    ) * 100
        else:
            revenue_growth = None

        if previous_quantity == 0 and recent_quantity > 0:
            performance_status = "New Sales / No Previous Baseline"

        elif quantity_growth is not None and quantity_growth > 10:
            performance_status = "Increasing"

        elif quantity_growth is not None and quantity_growth < -10:
            performance_status = "Declining"

        else:
            performance_status = "Stable"
        performance.append({
            "product_id": product.id,
            "product_name": product.product_name,
            "category": product.category,

            "recent_quantity": recent_quantity,
            "previous_quantity": previous_quantity,

            "recent_revenue": float(recent_revenue),
            "previous_revenue": float(previous_revenue),

            "quantity_growth_percent": (
    round(quantity_growth, 2)
    if quantity_growth is not None
    else None
),

"revenue_growth_percent": (
    round(revenue_growth, 2)
    if revenue_growth is not None
    else None
),

            "stock": product.stock,

            "performance_status": performance_status
        })

    # Highest revenue first
    performance.sort(
        key=lambda x: x["recent_revenue"],
        reverse=True
    )

    return {
        "business_id": business_id,
        "business_name": business.business_name,
        "latest_sale_date": latest_date,
        "period_days": period_days,
        "products": performance
    }