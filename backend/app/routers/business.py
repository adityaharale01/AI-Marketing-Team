from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.oauth2 import get_current_user
from app.dependencies import get_owned_business
from app.models.business import Business
from app.models.user import User
from app.schemas.business import (
    BusinessCreate,
    BusinessUpdate,
    BusinessResponse
)
from app.services.business_services import BusinessService

router = APIRouter(
    prefix="/business",
    tags=["Business"]
)


@router.post(
    "/",
    response_model=BusinessResponse,
    status_code=status.HTTP_201_CREATED
)
def create_business(
    business: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return BusinessService.create_business(
        db=db,
        owner_id=current_user.id,
        business=business
    )


@router.get(
    "/",
    response_model=list[BusinessResponse]
)
def get_my_businesses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return BusinessService.get_my_businesses(
        db=db,
        owner_id=current_user.id
    )


@router.get(
    "/{business_id}",
    response_model=BusinessResponse
)
def get_business(
    db: Session = Depends(get_db),
    owned_business: Business = Depends(get_owned_business)
):
    return owned_business


@router.put(
    "/{business_id}",
    response_model=BusinessResponse
)
def update_business(
    business: BusinessUpdate,
    db: Session = Depends(get_db),
    owned_business: Business = Depends(get_owned_business)
):
    return BusinessService.update_business(
        db=db,
        business_id=owned_business.id,
        business=business
    )


@router.delete(
    "/{business_id}",
    status_code=status.HTTP_200_OK
)
def delete_business(
    db: Session = Depends(get_db),
    owned_business: Business = Depends(get_owned_business)
):
    return BusinessService.delete_business(
        db=db,
        business_id=owned_business.id
    )