from app.database import SessionLocal
from app.services.rag_service import index_sales_summary


db = SessionLocal()

try:

    print("Indexing Business 2...")

    result = index_sales_summary(
        db,
        business_id=2
    )

    print(result)

    print("Indexing Business 3...")

    result = index_sales_summary(
        db,
        business_id=3
    )

    print(result)

finally:
    db.close()