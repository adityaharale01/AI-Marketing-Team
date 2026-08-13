from sqlalchemy.orm import Session

from app.models.campaign_content import CampaignContent
from app.schemas.campaign_content import (
    CampaignContentCreate,
    CampaignContentUpdate
)


class CampaignContentRepository:

    @staticmethod
    def create(
        db: Session,
        campaign_id: int,
        content_data: CampaignContentCreate
    ):

        db_content = CampaignContent(
            campaign_id=campaign_id,
            **content_data.model_dump()
        )

        db.add(db_content)
        db.commit()
        db.refresh(db_content)

        return db_content

    @staticmethod
    def get_all(
        db: Session,
        campaign_id: int
    ):

        return (
            db.query(CampaignContent)
            .filter(
                CampaignContent.campaign_id == campaign_id
            )
            .order_by(
                CampaignContent.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        content_id: int,
        campaign_id: int
    ):

        return (
            db.query(CampaignContent)
            .filter(
                CampaignContent.id == content_id,
                CampaignContent.campaign_id == campaign_id
            )
            .first()
        )

    @staticmethod
    def get_by_type(
        db: Session,
        campaign_id: int,
        content_type: str
    ):

        return (
            db.query(CampaignContent)
            .filter(
                CampaignContent.campaign_id == campaign_id,
                CampaignContent.content_type == content_type
            )
            .order_by(
                CampaignContent.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        db_content: CampaignContent,
        content_data: CampaignContentUpdate
    ):

        update_data = content_data.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(
                db_content,
                key,
                value
            )

        db.commit()
        db.refresh(db_content)

        return db_content

    @staticmethod
    def delete(
        db: Session,
        db_content: CampaignContent
    ):

        db.delete(db_content)
        db.commit()