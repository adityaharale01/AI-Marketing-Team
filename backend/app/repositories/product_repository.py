from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductRepository:

    @staticmethod
    def create(
        db: Session,
        business_id: int,
        product_data: ProductCreate
    ):
        db_product = Product(
            business_id=business_id,
            **product_data.model_dump()
        )

        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        return db_product

    @staticmethod
    def get_all(
        db: Session,
        business_id: int
    ):
        return (
            db.query(Product)
            .filter(Product.business_id == business_id)
            .order_by(Product.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        product_id: int,
        business_id: int
    ):
        return (
            db.query(Product)
            .filter(
                Product.id == product_id,
                Product.business_id == business_id
            )
            .first()
        )

    @staticmethod
    def get_by_sku(
        db: Session,
        sku: str,
        business_id: int
    ):
        return (
            db.query(Product)
            .filter(
                Product.sku == sku,
                Product.business_id == business_id
            )
            .first()
        )

    @staticmethod
    def search(
        db: Session,
        business_id: int,
        name: str
    ):
        return (
            db.query(Product)
            .filter(
                Product.business_id == business_id,
                Product.product_name.ilike(f"%{name}%")
            )
            .order_by(Product.product_name.asc())
            .all()
        )

    @staticmethod
    def get_by_category(
        db: Session,
        business_id: int,
        category: str
    ):
        return (
            db.query(Product)
            .filter(
                Product.business_id == business_id,
                Product.category.ilike(category)
            )
            .order_by(Product.product_name.asc())
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        db_product: Product,
        product_data: ProductUpdate
    ):
        update_data = product_data.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(db_product, key, value)

        db.commit()
        db.refresh(db_product)

        return db_product

    @staticmethod
    def delete(
        db: Session,
        db_product: Product
    ):
        db.delete(db_product)
        db.commit()