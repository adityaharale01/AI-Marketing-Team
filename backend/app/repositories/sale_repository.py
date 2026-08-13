from sqlalchemy.orm import Session

from app.models.sale import Sale
from app.schemas.sale import SaleCreate, SaleUpdate


class SaleRepository:

    @staticmethod
    def create(
        db: Session,
        business_id: int,
        sale_data: SaleCreate
    ):
        total_amount = sale_data.quantity * sale_data.unit_price

        db_sale = Sale(
            business_id=business_id,
            product_id=sale_data.product_id,
            quantity=sale_data.quantity,
            unit_price=sale_data.unit_price,
            total_amount=total_amount,
            sale_date=sale_data.sale_date
        )

        db.add(db_sale)
        db.commit()
        db.refresh(db_sale)

        return db_sale

    @staticmethod
    def get_by_id(
        db: Session,
        sale_id: int,
        business_id: int
    ):
        return (
            db.query(Sale)
            .filter(
                Sale.id == sale_id,
                Sale.business_id == business_id
            )
            .first()
        )

    @staticmethod
    def get_all(
        db: Session,
        business_id: int
    ):
        return (
            db.query(Sale)
            .filter(Sale.business_id == business_id)
            .order_by(Sale.sale_date.desc())
            .all()
        )

    @staticmethod
    def get_by_product(
        db: Session,
        business_id: int,
        product_id: int
    ):
        return (
            db.query(Sale)
            .filter(
                Sale.business_id == business_id,
                Sale.product_id == product_id
            )
            .order_by(Sale.sale_date.desc())
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        db_sale: Sale,
        sale_data: SaleUpdate
    ):
        update_data = sale_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(db_sale, key, value)

        # Recalculate total after update
        db_sale.total_amount = (
            db_sale.quantity * db_sale.unit_price
        )

        db.commit()
        db.refresh(db_sale)

        return db_sale

    @staticmethod
    def delete(
        db: Session,
        db_sale: Sale
    ):
        db.delete(db_sale)
        db.commit()