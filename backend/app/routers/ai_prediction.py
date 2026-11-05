from fastapi import (
    APIRouter,
    Depends,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_active_business
from app.models.business import Business

from app.schemas.ai_prediction import (
    AIPredictionCreate,
    AIPredictionResponse
)

from app.services.ai_prediction_service import (
    AIPredictionService
)


router = APIRouter(
    prefix="/ai-predictions",
    tags=["AI Predictions"]
)


@router.post(
    "/",
    response_model=AIPredictionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_prediction(
    prediction: AIPredictionCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return AIPredictionService.create_prediction(
        db=db,
        business_id=business.id,
        prediction_data=prediction
    )


@router.get(
    "/",
    response_model=list[AIPredictionResponse]
)
def get_predictions(
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return AIPredictionService.get_predictions(
        db=db,
        business_id=business.id
    )


@router.get(
    "/product/{product_id}",
    response_model=list[AIPredictionResponse]
)
def get_product_predictions(
    product_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return AIPredictionService.get_product_predictions(
        db=db,
        product_id=product_id,
        business_id=business.id
    )


@router.get(
    "/{prediction_id}",
    response_model=AIPredictionResponse
)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return AIPredictionService.get_prediction(
        db=db,
        prediction_id=prediction_id,
        business_id=business.id
    )


@router.delete(
    "/{prediction_id}"
)
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return AIPredictionService.delete_prediction(
        db=db,
        prediction_id=prediction_id,
        business_id=business.id
    )