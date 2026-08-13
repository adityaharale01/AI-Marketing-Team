from sqlalchemy.orm import Session

from app.models.ai_prediction import AIPrediction
from app.schemas.ai_prediction import AIPredictionCreate


class AIPredictionRepository:

    @staticmethod
    def create(
        db: Session,
        business_id: int,
        prediction_data: AIPredictionCreate
    ):

        db_prediction = AIPrediction(
            business_id=business_id,
            **prediction_data.model_dump()
        )

        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)

        return db_prediction

    @staticmethod
    def get_all(
        db: Session,
        business_id: int
    ):

        return (
            db.query(AIPrediction)
            .filter(
                AIPrediction.business_id == business_id
            )
            .order_by(
                AIPrediction.prediction_date.desc()
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        prediction_id: int,
        business_id: int
    ):

        return (
            db.query(AIPrediction)
            .filter(
                AIPrediction.id == prediction_id,
                AIPrediction.business_id == business_id
            )
            .first()
        )

    @staticmethod
    def get_by_product(
        db: Session,
        product_id: int,
        business_id: int
    ):

        return (
            db.query(AIPrediction)
            .filter(
                AIPrediction.product_id == product_id,
                AIPrediction.business_id == business_id
            )
            .order_by(
                AIPrediction.prediction_date.desc()
            )
            .all()
        )

    @staticmethod
    def delete(
        db: Session,
        prediction: AIPrediction
    ):

        db.delete(prediction)
        db.commit()