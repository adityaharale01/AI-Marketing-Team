from datetime import timedelta, datetime
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
        products = db.query(Product).filter(Product.business_id == business_id).all()
        return {
            "business_id": business_id,
            "business_name": business.business_name,
            "business_category": getattr(business, "business_type", getattr(business, "category", None)),
            "product_count": len(products),
            "latest_sale_date": None,
            "message": "No sales data available for this business.",
            "overall": {
                "recent_quantity": 0, "previous_quantity": 0,
                "recent_revenue": 0.0, "previous_revenue": 0.0,
                "quantity_growth_percent": None, "revenue_growth_percent": None,
            },
            "products": [{
                "product_id": product.id,
                "product_name": product.product_name,
                "category": getattr(product, "category", None),
                "recent_quantity": 0, "previous_quantity": 0,
                "recent_revenue": 0.0, "previous_revenue": 0.0,
                "revenue_growth_percent": None, "growth_percent": None,
                "stock": int(product.stock or 0),
                "status": "No Sales Data", "performance_label": "No sales data available",
            } for product in products],
            "daily_sales": [], "highest_sales_date": None,
            "average_daily_revenue": 0.0,
            "calendar_month_comparison": None,
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


    # Daily sales summary for evidence-based peak-day and average-revenue answers.
    daily_totals = {}
    for sale in recent_sales:
        day = sale.sale_date.date().isoformat()
        bucket = daily_totals.setdefault(day, {"revenue": 0.0, "quantity": 0})
        bucket["revenue"] += float(sale.total_amount or Decimal("0"))
        bucket["quantity"] += int(sale.quantity or 0)

    daily_sales = [
        {"date": day, "revenue": round(values["revenue"], 2), "quantity": values["quantity"]}
        for day, values in sorted(daily_totals.items())
    ]

    # Calendar-month comparison is anchored to the latest available sale date,
    # so stale demo data does not silently compare against today's empty month.
    month_anchor = latest_date.date() if hasattr(latest_date, "date") else latest_date
    month_start = month_anchor.replace(day=1)
    if month_start.month == 1:
        previous_month_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        previous_month_start = month_start.replace(month=month_start.month - 1)
    all_business_sales = db.query(Sale).filter(Sale.business_id == business_id).all()
    current_month_sales = [s for s in all_business_sales if month_start <= s.sale_date.date() <= month_anchor] if hasattr(latest_date, "date") else []
    previous_month_sales = [s for s in all_business_sales if previous_month_start <= s.sale_date.date() < month_start] if hasattr(latest_date, "date") else []
    current_month_revenue = sum((s.total_amount or Decimal("0")) for s in current_month_sales)
    previous_month_revenue = sum((s.total_amount or Decimal("0")) for s in previous_month_sales)
    current_month_quantity = sum(int(s.quantity or 0) for s in current_month_sales)
    previous_month_quantity = sum(int(s.quantity or 0) for s in previous_month_sales)

    all_time_dates = {}
    for sale in all_business_sales:
        day = sale.sale_date.date().isoformat()
        all_time_dates.setdefault(day, 0.0)
        all_time_dates[day] += float(sale.total_amount or Decimal("0"))
    highest_sales_date = max(all_time_dates.items(), key=lambda item: item[1]) if all_time_dates else None

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
        previous_product_revenue = sum(
            (sale.total_amount or Decimal("0"))
            for sale in product_previous_sales
        )
        product_revenue_growth = (
            ((float(recent_product_revenue) - float(previous_product_revenue))
             / float(previous_product_revenue)) * 100
            if previous_product_revenue > 0 else None
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


# Determine product status
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
            "previous_revenue": float(previous_product_revenue),
            "revenue_growth_percent": round(product_revenue_growth, 2) if product_revenue_growth is not None else None,
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
        "business_category": getattr(business, "business_type", getattr(business, "category", None)),
        "latest_sale_date": latest_date,
        "period_days": period_days,
        "product_count": len(products),
        "daily_sales": daily_sales,
        "highest_sales_date": ({"date": highest_sales_date[0], "revenue": round(highest_sales_date[1], 2)} if highest_sales_date else None),
        "average_daily_revenue": round(float(recent_revenue) / period_days, 2),
        "calendar_month_comparison": {
            "month": month_start.isoformat(),
            "previous_month": previous_month_start.isoformat(),
            "recent_revenue": float(current_month_revenue),
            "previous_revenue": float(previous_month_revenue),
            "recent_quantity": current_month_quantity,
            "previous_quantity": previous_month_quantity,
            "revenue_change": float(current_month_revenue - previous_month_revenue),
            "quantity_change": current_month_quantity - previous_month_quantity,
            "revenue_growth_percent": round(((float(current_month_revenue) - float(previous_month_revenue)) / float(previous_month_revenue)) * 100, 2) if previous_month_revenue else None,
            "quantity_growth_percent": round(((current_month_quantity - previous_month_quantity) / previous_month_quantity) * 100, 2) if previous_month_quantity else None,
        },

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