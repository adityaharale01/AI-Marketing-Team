from fastapi import (
    APIRouter,
    Depends,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_active_business
from app.models.business import Business

from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse
)

from app.services.product_service import ProductService


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    return ProductService.create_product(
        db=db,
        business_id=business.id,
        product_data=product
    )


@router.get(
    "/",
    response_model=list[ProductResponse]
)
def get_products(
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    return ProductService.get_products(
        db=db,
        business_id=business.id
    )


@router.get(
    "/search",
    response_model=list[ProductResponse]
)
def search_products(
    name: str,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    return ProductService.search_products(
        db=db,
        business_id=business.id,
        name=name
    )


@router.get(
    "/category/{category}",
    response_model=list[ProductResponse]
)
def get_products_by_category(
    category: str,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    return ProductService.get_products_by_category(
        db=db,
        business_id=business.id,
        category=category
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    return ProductService.get_product(
        db=db,
        product_id=product_id,
        business_id=business.id
    )


@router.put(
    "/{product_id}",
    response_model=ProductResponse
)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    return ProductService.update_product(
        db=db,
        product_id=product_id,
        business_id=business.id,
        product_data=product
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):
    return ProductService.delete_product(
        db=db,
        product_id=product_id,
        business_id=business.id
    )