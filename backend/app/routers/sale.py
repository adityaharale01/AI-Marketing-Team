from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_active_business
from app.models.business import Business

from app.schemas.sale import (
    SaleCreate,
    SaleUpdate,
    SaleResponse
)

from app.services.sale_service import SaleService

router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)


@router.post(
    "/",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_sale(
    sale: SaleCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    """
    Create a new sale for the current user's business.
    """

    return SaleService.create_sale(
        db=db,
        business_id=business.id,
        sale_data=sale
    )


@router.get(
    "/",
    response_model=list[SaleResponse]
)
def get_sales(
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    """
    Get all sales belonging to the current user's business.
    """

    return SaleService.get_sales(
        db=db,
        business_id=business.id
    )


@router.get(
    "/product/{product_id}",
    response_model=list[SaleResponse]
)
def get_product_sales(
    product_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    """
    Get sales for a specific product.
    """

    return SaleService.get_product_sales(
        db=db,
        business_id=business.id,
        product_id=product_id
    )


@router.get(
    "/{sale_id}",
    response_model=SaleResponse
)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    """
    Get a specific sale.
    """

    return SaleService.get_sale(
        db=db,
        sale_id=sale_id,
        business_id=business.id
    )


@router.put(
    "/{sale_id}",
    response_model=SaleResponse
)
def update_sale(
    sale_id: int,
    sale: SaleUpdate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    """
    Update a sale.
    """

    return SaleService.update_sale(
        db=db,
        sale_id=sale_id,
        business_id=business.id,
        sale_data=sale
    )


@router.delete(
    "/{sale_id}",
    status_code=status.HTTP_200_OK
)
def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    """
    Delete a sale.
    """

    return SaleService.delete_sale(
        db=db,
        sale_id=sale_id,
        business_id=business.id
    )