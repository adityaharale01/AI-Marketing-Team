from sqlalchemy.orm import Session

from app.models.business import Business
from app.schemas.business import BusinessCreate, BusinessUpdate


class BusinessRepository:

    @staticmethod
    def create(db: Session, owner_id: int, business: BusinessCreate):
        db_business = Business(
            owner_id=owner_id,
            **business.model_dump()
        )

        db.add(db_business)
        db.commit()
        db.refresh(db_business)

        return db_business

    @staticmethod
    def get_all(db: Session):
        return db.query(Business).all()

    @staticmethod
    def get_by_id(db: Session, business_id: int):
        return (
            db.query(Business)
            .filter(Business.id == business_id)
            .first()
        )

    @staticmethod
    def get_by_owner(db: Session, owner_id: int):
        return (
            db.query(Business)
            .filter(Business.owner_id == owner_id)
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        db_business: Business,
        business: BusinessUpdate
    ):

        update_data = business.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(db_business, key, value)

        db.commit()
        db.refresh(db_business)

        return db_business

    @staticmethod
    def delete(db: Session, db_business: Business):

        db.delete(db_business)

        db.commit()

        return True