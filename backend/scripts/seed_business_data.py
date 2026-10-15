from app.models import (
    User,
    Business,
    Product,
    Sale,
    Campaign,
    CampaignContent,
    AIInteraction,
    AIPrediction
)

from app.database import SessionLocal
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.business import Business
from app.models.product import Product


PRODUCTS = {
    2: [
        {
            "product_name": "Chocolate Cake",
            "category": "Cakes",
            "description": "Rich chocolate cake with chocolate cream.",
            "price": 550,
            "stock": 0,
        },
        {
            "product_name": "Black Forest Cake",
            "category": "Cakes",
            "description": "Classic black forest cake with cherries and cream.",
            "price": 650,
            "stock": 18,
        },
        {
            "product_name": "Red Velvet Cake",
            "category": "Cakes",
            "description": "Soft red velvet cake with cream cheese frosting.",
            "price": 700,
            "stock": 12,
        },
        {
            "product_name": "Vanilla Cake",
            "category": "Cakes",
            "description": "Soft vanilla sponge cake with fresh cream.",
            "price": 450,
            "stock": 35,
        },
        {
            "product_name": "Pineapple Cake",
            "category": "Cakes",
            "description": "Fresh pineapple cake with cream.",
            "price": 500,
            "stock": 22,
        },
        {
            "product_name": "Butterscotch Cake",
            "category": "Cakes",
            "description": "Butterscotch cake with caramel crunch.",
            "price": 600,
            "stock": 16,
        },
        {
            "product_name": "Chocolate Brownie",
            "category": "Brownies",
            "description": "Dense and rich chocolate brownie.",
            "price": 120,
            "stock": 40,
        },
        {
            "product_name": "Walnut Brownie",
            "category": "Brownies",
            "description": "Chocolate brownie topped with walnuts.",
            "price": 150,
            "stock": 30,
        },
        {
            "product_name": "Chocolate Chip Cookies",
            "category": "Cookies",
            "description": "Crispy cookies with chocolate chips.",
            "price": 180,
            "stock": 50,
        },
        {
            "product_name": "Butter Cookies",
            "category": "Cookies",
            "description": "Classic buttery cookies.",
            "price": 160,
            "stock": 45,
        },
        {
            "product_name": "Croissant",
            "category": "Pastries",
            "description": "Freshly baked buttery croissant.",
            "price": 90,
            "stock": 25,
        },
        {
            "product_name": "Chocolate Croissant",
            "category": "Pastries",
            "description": "Flaky croissant filled with chocolate.",
            "price": 120,
            "stock": 20,
        },
        {
            "product_name": "Garlic Bread",
            "category": "Breads",
            "description": "Fresh garlic bread with herbs.",
            "price": 140,
            "stock": 28,
        },
        {
            "product_name": "Milk Bread",
            "category": "Breads",
            "description": "Soft fresh milk bread.",
            "price": 70,
            "stock": 35,
        },
        {
            "product_name": "Brown Bread",
            "category": "Breads",
            "description": "Healthy whole wheat brown bread.",
            "price": 65,
            "stock": 32,
        },
        {
            "product_name": "Veg Sandwich",
            "category": "Snacks",
            "description": "Fresh vegetable sandwich.",
            "price": 130,
            "stock": 20,
        },
        {
            "product_name": "Cheese Sandwich",
            "category": "Snacks",
            "description": "Grilled sandwich with cheese and vegetables.",
            "price": 160,
            "stock": 18,
        },
        {
            "product_name": "Muffin",
            "category": "Pastries",
            "description": "Soft freshly baked vanilla muffin.",
            "price": 80,
            "stock": 35,
        },
        {
            "product_name": "Chocolate Muffin",
            "category": "Pastries",
            "description": "Chocolate muffin with chocolate chips.",
            "price": 100,
            "stock": 30,
        },
        {
            "product_name": "Fruit Tart",
            "category": "Desserts",
            "description": "Fresh fruit tart with cream filling.",
            "price": 220,
            "stock": 15,
        },
    ],

    3: [
        {
            "product_name": "Strawberry Cake",
            "category": "Cakes",
            "description": "Fresh strawberry cake with whipped cream.",
            "price": 650,
            "stock": 20,
        },
        {
            "product_name": "Mango Cake",
            "category": "Cakes",
            "description": "Seasonal mango cake with fresh mango.",
            "price": 700,
            "stock": 15,
        },
        {
            "product_name": "Coffee Cake",
            "category": "Cakes",
            "description": "Coffee-flavored cake with creamy frosting.",
            "price": 580,
            "stock": 24,
        },
        {
            "product_name": "Caramel Cake",
            "category": "Cakes",
            "description": "Soft caramel cake with caramel topping.",
            "price": 620,
            "stock": 18,
        },
        {
            "product_name": "Fruit Cake",
            "category": "Cakes",
            "description": "Mixed fruit cake with nuts.",
            "price": 600,
            "stock": 25,
        },
        {
            "product_name": "Cheesecake",
            "category": "Desserts",
            "description": "Creamy baked cheesecake.",
            "price": 750,
            "stock": 10,
        },
        {
            "product_name": "Blueberry Cheesecake",
            "category": "Desserts",
            "description": "Cheesecake topped with blueberry sauce.",
            "price": 800,
            "stock": 8,
        },
        {
            "product_name": "Chocolate Fudge",
            "category": "Desserts",
            "description": "Rich chocolate fudge dessert.",
            "price": 180,
            "stock": 35,
        },
        {
            "product_name": "Donut",
            "category": "Pastries",
            "description": "Fresh glazed donut.",
            "price": 70,
            "stock": 50,
        },
        {
            "product_name": "Chocolate Donut",
            "category": "Pastries",
            "description": "Chocolate glazed donut.",
            "price": 90,
            "stock": 45,
        },
        {
            "product_name": "Cinnamon Roll",
            "category": "Pastries",
            "description": "Soft cinnamon roll with icing.",
            "price": 130,
            "stock": 25,
        },
        {
            "product_name": "Paneer Puff",
            "category": "Snacks",
            "description": "Crispy puff filled with spiced paneer.",
            "price": 80,
            "stock": 40,
        },
        {
            "product_name": "Veg Puff",
            "category": "Snacks",
            "description": "Crispy puff filled with vegetables.",
            "price": 60,
            "stock": 45,
        },
        {
            "product_name": "Cheese Puff",
            "category": "Snacks",
            "description": "Golden puff filled with cheese.",
            "price": 90,
            "stock": 30,
        },
        {
            "product_name": "French Baguette",
            "category": "Breads",
            "description": "Fresh crusty French baguette.",
            "price": 120,
            "stock": 20,
        },
        {
            "product_name": "Multigrain Bread",
            "category": "Breads",
            "description": "Healthy multigrain bread.",
            "price": 100,
            "stock": 35,
        },
        {
            "product_name": "Garlic Bun",
            "category": "Breads",
            "description": "Soft bun with garlic butter.",
            "price": 75,
            "stock": 40,
        },
        {
            "product_name": "Oat Cookies",
            "category": "Cookies",
            "description": "Healthy cookies made with oats.",
            "price": 170,
            "stock": 40,
        },
        {
            "product_name": "Almond Cookies",
            "category": "Cookies",
            "description": "Crunchy cookies with almonds.",
            "price": 200,
            "stock": 30,
        },
        {
            "product_name": "Chocolate Eclair",
            "category": "Pastries",
            "description": "Cream-filled pastry topped with chocolate.",
            "price": 140,
            "stock": 20,
        },
    ],
}


def generate_sku(business_id, product_name):
    clean_name = "".join(
        character
        for character in product_name.upper()
        if character.isalnum()
    )

    return f"B{business_id}-{clean_name[:10]}"


def seed_products():
    db: Session = SessionLocal()

    try:
        for business_id, products in PRODUCTS.items():

            business = (
                db.query(Business)
                .filter(Business.id == business_id)
                .first()
            )

            if not business:
                print(f"Business {business_id} not found. Skipping.")
                continue

            print(
                f"\nProcessing: {business.business_name} "
                f"(ID {business_id})"
            )

            for product_data in products:

                existing = (
                    db.query(Product)
                    .filter(
                        Product.business_id == business_id,
                        Product.product_name
                        == product_data["product_name"]
                    )
                    .first()
                )

                if existing:
                    print(
                        f"  EXISTS: "
                        f"{product_data['product_name']}"
                    )
                    continue

                product = Product(
                    business_id=business_id,
                    product_name=product_data["product_name"],
                    category=product_data["category"],
                    description=product_data["description"],
                    sku=generate_sku(
                        business_id,
                        product_data["product_name"]
                    ),
                    price=product_data["price"],
                    stock=product_data["stock"],
                    is_active=True
                )

                db.add(product)

                print(
                    f"  ADDED: "
                    f"{product_data['product_name']}"
                )

        db.commit()

        print("\n================================")
        print("PRODUCT SEEDING COMPLETED")
        print("================================")

    except Exception as e:
        db.rollback()
        print("\nERROR:")
        print(e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_products()