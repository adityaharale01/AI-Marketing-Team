from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.business_repository import BusinessRepository
from app.schemas.business import BusinessCreate, BusinessUpdate


class BusinessService:

    @staticmethod
    def create_business(
        db: Session,
        owner_id: int,
        business: BusinessCreate
    ):

        return BusinessRepository.create(
            db,
            owner_id,
            business
        )

    @staticmethod
    def get_all_businesses(db: Session):

        return BusinessRepository.get_all(db)

    @staticmethod
    def get_business_by_id(
        db: Session,
        business_id: int
    ):

        business = BusinessRepository.get_by_id(
            db,
            business_id
        )

        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )

        return business

    @staticmethod
    def get_my_businesses(
        db: Session,
        owner_id: int
    ):

        return BusinessRepository.get_by_owner(
            db,
            owner_id
        )

    @staticmethod
    def update_business(
        db: Session,
        business_id: int,
        business: BusinessUpdate
    ):

        db_business = BusinessRepository.get_by_id(
            db,
            business_id
        )

        if not db_business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )

        return BusinessRepository.update(
            db,
            db_business,
            business
        )

    @staticmethod
    def delete_business(
        db: Session,
        business_id: int
    ):

        db_business = BusinessRepository.get_by_id(
            db,
            business_id
        )

        if not db_business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )

        BusinessRepository.delete(
            db,
            db_business
        )

        return {
            "message": "Business deleted successfully"
        }