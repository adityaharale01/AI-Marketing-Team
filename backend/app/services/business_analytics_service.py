from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.product import Product
from app.models.sale import Sale


def get_business_analytics(
    db: Session,
    business_id: int,
    period_days: int = 7
):
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
            "message": "No sales data available."
        }

    latest_date = latest_sale[0]

    recent_start = latest_date - timedelta(days=period_days)
    previous_start = latest_date - timedelta(days=period_days * 2)

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
        sale for sale in sales
        if sale.sale_date > recent_start
    ]

    previous_sales = [
        sale for sale in sales
        if sale.sale_date <= recent_start
    ]

    recent_quantity = sum(
        sale.quantity for sale in recent_sales
    )

    previous_quantity = sum(
        sale.quantity for sale in previous_sales
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

    products = (
        db.query(Product)
        .filter(Product.business_id == business_id)
        .all()
    )

    product_analytics = []

    for product in products:

        product_recent_sales = [
            sale for sale in recent_sales
            if sale.product_id == product.id
        ]

        product_previous_sales = [
            sale for sale in previous_sales
            if sale.product_id == product.id
        ]

        recent_product_quantity = sum(
            sale.quantity
            for sale in product_recent_sales
        )

        previous_product_quantity = sum(
            sale.quantity
            for sale in product_previous_sales
        )

        recent_product_revenue = sum(
            (sale.total_amount or Decimal("0"))
            for sale in product_recent_sales
        )

        if previous_product_quantity > 0:
            product_growth = (
                (
                    recent_product_quantity
                    - previous_product_quantity
                )
                / previous_product_quantity
            ) * 100
        else:
            product_growth = None

            if previous_product_quantity == 0 and recent_product_quantity > 0:
                status = "New Sales / No Previous Baseline"
                performance_label = "Cannot determine growth"

            elif product_growth is not None and product_growth > 10:
                status = "Increasing"
                performance_label = "Performing well"

            elif product_growth is not None and product_growth < -10:
                    status = "Declining"
                    performance_label = "Needs attention"

            else:
               status = "Stable"
               performance_label = "Stable"

        product_analytics.append({
            "product_id": product.id,
            "product_name": product.product_name,
            "category": product.category,
            "recent_quantity": recent_product_quantity,
            "previous_quantity": previous_product_quantity,
            "recent_revenue": float(recent_product_revenue),
            "growth_percent": (
                round(product_growth, 2)
                if product_growth is not None
                else None
            ),
            "stock": product.stock,
            "status": status,
            "performance_label": performance_label
        })

    product_analytics.sort(
        key=lambda x: x["recent_revenue"],
        reverse=True
    )

    return {
        "business_id": business_id,
        "business_name": business.business_name,
        "latest_sale_date": latest_date,
        "period_days": period_days,

        "overall": {
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
            )
        },

        "products": product_analytics
    }