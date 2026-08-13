from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:

    @staticmethod
    def create_product(
        db: Session,
        business_id: int,
        product_data: ProductCreate
    ):
        # Check duplicate SKU
        existing_product = ProductRepository.get_by_sku(
            db=db,
            sku=product_data.sku,
            business_id=business_id
        )

        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product with this SKU already exists"
            )

        return ProductRepository.create(
            db=db,
            business_id=business_id,
            product_data=product_data
        )

    @staticmethod
    def get_products(
        db: Session,
        business_id: int
    ):
        return ProductRepository.get_all(
            db=db,
            business_id=business_id
        )

    @staticmethod
    def get_product(
        db: Session,
        product_id: int,
        business_id: int
    ):
        product = ProductRepository.get_by_id(
            db=db,
            product_id=product_id,
            business_id=business_id
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        return product

    @staticmethod
    def search_products(
        db: Session,
        business_id: int,
        name: str
    ):
        return ProductRepository.search(
            db=db,
            business_id=business_id,
            name=name
        )

    @staticmethod
    def get_products_by_category(
        db: Session,
        business_id: int,
        category: str
    ):
        return ProductRepository.get_by_category(
            db=db,
            business_id=business_id,
            category=category
        )

    @staticmethod
    def update_product(
        db: Session,
        product_id: int,
        business_id: int,
        product_data: ProductUpdate
    ):
        product = ProductRepository.get_by_id(
            db=db,
            product_id=product_id,
            business_id=business_id
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        # Check SKU uniqueness if SKU is being changed
        if product_data.sku is not None:
            existing_product = ProductRepository.get_by_sku(
                db=db,
                sku=product_data.sku,
                business_id=business_id
            )

            if (
                existing_product
                and existing_product.id != product_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Product with this SKU already exists"
                )

        return ProductRepository.update(
            db=db,
            db_product=product,
            product_data=product_data
        )

    @staticmethod
    def delete_product(
        db: Session,
        product_id: int,
        business_id: int
    ):
        product = ProductRepository.get_by_id(
            db=db,
            product_id=product_id,
            business_id=business_id
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        ProductRepository.delete(
            db=db,
            db_product=product
        )

        return {
            "message": "Product deleted successfully"
        }