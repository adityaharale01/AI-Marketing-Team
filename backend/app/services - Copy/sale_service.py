from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.sale_repository import SaleRepository
from app.schemas.sale import SaleCreate, SaleUpdate


class SaleService:

    @staticmethod
    def create_sale(
        db: Session,
        business_id: int,
        sale_data: SaleCreate
    ):
        return SaleRepository.create(
            db=db,
            business_id=business_id,
            sale_data=sale_data
        )

    @staticmethod
    def get_sales(
        db: Session,
        business_id: int
    ):
        return SaleRepository.get_all(
            db=db,
            business_id=business_id
        )

    @staticmethod
    def get_sale(
        db: Session,
        sale_id: int,
        business_id: int
    ):
        sale = SaleRepository.get_by_id(
            db=db,
            sale_id=sale_id,
            business_id=business_id
        )

        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found"
            )

        return sale

    @staticmethod
    def get_product_sales(
        db: Session,
        business_id: int,
        product_id: int
    ):
        return SaleRepository.get_by_product(
            db=db,
            business_id=business_id,
            product_id=product_id
        )

    @staticmethod
    def update_sale(
        db: Session,
        sale_id: int,
        business_id: int,
        sale_data: SaleUpdate
    ):
        sale = SaleRepository.get_by_id(
            db=db,
            sale_id=sale_id,
            business_id=business_id
        )

        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found"
            )

        return SaleRepository.update(
            db=db,
            db_sale=sale,
            sale_data=sale_data
        )

    @staticmethod
    def delete_sale(
        db: Session,
        sale_id: int,
        business_id: int
    ):
        sale = SaleRepository.get_by_id(
            db=db,
            sale_id=sale_id,
            business_id=business_id
        )

        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found"
            )

        SaleRepository.delete(
            db=db,
            db_sale=sale
        )

        return {
            "message": "Sale deleted successfully"
        }