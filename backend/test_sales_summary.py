from app.database import SessionLocal
from app.services.sales_summary_service import get_sales_summary


db = SessionLocal()

try:

    result = get_sales_summary(
        db,
        business_id=2,
        period_days=30
    )

    print("\n==============================")
    print("SALES SUMMARY")
    print("==============================")

    print(result)

finally:
    db.close()