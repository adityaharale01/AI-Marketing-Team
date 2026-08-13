from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate
)


class CampaignRepository:

    @staticmethod
    def create(
        db: Session,
        business_id: int,
        campaign_data: CampaignCreate
    ):

        db_campaign = Campaign(
            business_id=business_id,
            **campaign_data.model_dump()
        )

        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)

        return db_campaign

    @staticmethod
    def get_all(
        db: Session,
        business_id: int
    ):

        return (
            db.query(Campaign)
            .filter(
                Campaign.business_id == business_id
            )
            .order_by(
                Campaign.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        campaign_id: int,
        business_id: int
    ):

        return (
            db.query(Campaign)
            .filter(
                Campaign.id == campaign_id,
                Campaign.business_id == business_id
            )
            .first()
        )

    @staticmethod
    def get_by_status(
        db: Session,
        business_id: int,
        status: str
    ):

        return (
            db.query(Campaign)
            .filter(
                Campaign.business_id == business_id,
                Campaign.status == status
            )
            .order_by(
                Campaign.start_date.desc()
            )
            .all()
        )

    @staticmethod
    def search(
        db: Session,
        business_id: int,
        name: str
    ):

        return (
            db.query(Campaign)
            .filter(
                Campaign.business_id == business_id,
                Campaign.campaign_name.ilike(
                    f"%{name}%"
                )
            )
            .order_by(
                Campaign.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        db_campaign: Campaign,
        campaign_data: CampaignUpdate
    ):

        update_data = campaign_data.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(
                db_campaign,
                key,
                value
            )

        db.commit()
        db.refresh(db_campaign)

        return db_campaign

    @staticmethod
    def delete(
        db: Session,
        db_campaign: Campaign
    ):

        db.delete(db_campaign)
        db.commit()