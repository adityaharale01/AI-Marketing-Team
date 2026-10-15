from datetime import datetime, timedelta
import random

from app.database import SessionLocal
from app.models.business import Business
from app.models.product import Product
from app.models.sale import Sale


db = SessionLocal()

try:
    businesses = db.query(Business).filter(
        Business.id.in_([2, 3])
    ).all()

    if not businesses:
        print("No businesses found.")
        exit()

    total_added = 0

    for business in businesses:

        print(f"\nProcessing: {business.business_name} (ID {business.id})")

        products = db.query(Product).filter(
            Product.business_id == business.id,
            Product.is_active == True
        ).all()

        if not products:
            print("No products found.")
            continue

        print(f"Products found: {len(products)}")

        # 60 days of sales history
        for product in products:

            for day in range(60):

                sale_date = datetime.now() - timedelta(days=59 - day)

                # Create 0-3 sales entries per day
                number_of_sales = random.randint(0, 3)

                for _ in range(number_of_sales):

                    quantity = random.randint(1, 5)

                    # Different demand patterns
                    if product.product_name in [
                        "Chocolate Cake",
                        "Black Forest Cake",
                        "Red Velvet Cake"
                    ]:
                        quantity += random.randint(1, 3)

                    elif "Cookie" in product.product_name:
                        quantity += random.randint(0, 2)

                    unit_price = float(product.price)

                    total_amount = quantity * unit_price

                    sale = Sale(
                        business_id=business.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_amount=total_amount,
                        sale_date=sale_date
                    )

                    db.add(sale)
                    total_added += 1

        db.commit()

    print("\n================================")
    print("SALES SEEDING COMPLETED")
    print("================================")
    print(f"Total sales records added: {total_added}")

except Exception as e:
    db.rollback()
    print("\nERROR:", e)

finally:
    db.close()