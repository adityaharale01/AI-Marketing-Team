from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.ai_prediction_repository import (
    AIPredictionRepository
)

from app.repositories.product_repository import (
    ProductRepository
)

from app.schemas.ai_prediction import (
    AIPredictionCreate
)


class AIPredictionService:

    @staticmethod
    def create_prediction(
        db: Session,
        business_id: int,
        prediction_data: AIPredictionCreate
    ):

        # Make sure product belongs to this business
        product = ProductRepository.get_by_id(
            db=db,
            product_id=prediction_data.product_id,
            business_id=business_id
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found for this business"
            )

        return AIPredictionRepository.create(
            db=db,
            business_id=business_id,
            prediction_data=prediction_data
        )

    @staticmethod
    def get_predictions(
        db: Session,
        business_id: int
    ):

        return AIPredictionRepository.get_all(
            db=db,
            business_id=business_id
        )

    @staticmethod
    def get_prediction(
        db: Session,
        prediction_id: int,
        business_id: int
    ):

        prediction = AIPredictionRepository.get_by_id(
            db=db,
            prediction_id=prediction_id,
            business_id=business_id
        )

        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI prediction not found"
            )

        return prediction

    @staticmethod
    def get_product_predictions(
        db: Session,
        product_id: int,
        business_id: int
    ):

        # Check product belongs to business
        product = ProductRepository.get_by_id(
            db=db,
            product_id=product_id,
            business_id=business_id
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found for this business"
            )

        return AIPredictionRepository.get_by_product(
            db=db,
            product_id=product_id,
            business_id=business_id
        )

    @staticmethod
    def delete_prediction(
        db: Session,
        prediction_id: int,
        business_id: int
    ):

        prediction = AIPredictionRepository.get_by_id(
            db=db,
            prediction_id=prediction_id,
            business_id=business_id
        )

        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI prediction not found"
            )

        AIPredictionRepository.delete(
            db=db,
            prediction=prediction
        )

        return {
            "message": "AI prediction deleted successfully"
        }