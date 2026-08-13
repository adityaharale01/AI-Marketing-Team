from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.campaign_content_repository import (
    CampaignContentRepository
)

from app.repositories.campaign_repository import (
    CampaignRepository
)

from app.schemas.campaign_content import (
    CampaignContentCreate,
    CampaignContentUpdate
)


class CampaignContentService:

    @staticmethod
    def create_content(
        db: Session,
        campaign_id: int,
        business_id: int,
        content_data: CampaignContentCreate
    ):

        campaign = CampaignRepository.get_by_id(
            db=db,
            campaign_id=campaign_id,
            business_id=business_id
        )

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        return CampaignContentRepository.create(
            db=db,
            campaign_id=campaign_id,
            content_data=content_data
        )

    @staticmethod
    def get_contents(
        db: Session,
        campaign_id: int,
        business_id: int
    ):

        campaign = CampaignRepository.get_by_id(
            db=db,
            campaign_id=campaign_id,
            business_id=business_id
        )

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        return CampaignContentRepository.get_all(
            db=db,
            campaign_id=campaign_id
        )

    @staticmethod
    def get_content(
        db: Session,
        content_id: int,
        campaign_id: int,
        business_id: int
    ):

        campaign = CampaignRepository.get_by_id(
            db=db,
            campaign_id=campaign_id,
            business_id=business_id
        )

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        content = CampaignContentRepository.get_by_id(
            db=db,
            content_id=content_id,
            campaign_id=campaign_id
        )

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign content not found"
            )

        return content

    @staticmethod
    def get_by_type(
        db: Session,
        campaign_id: int,
        business_id: int,
        content_type: str
    ):

        campaign = CampaignRepository.get_by_id(
            db=db,
            campaign_id=campaign_id,
            business_id=business_id
        )

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        return CampaignContentRepository.get_by_type(
            db=db,
            campaign_id=campaign_id,
            content_type=content_type
        )

    @staticmethod
    def update_content(
        db: Session,
        content_id: int,
        campaign_id: int,
        business_id: int,
        content_data: CampaignContentUpdate
    ):

        campaign = CampaignRepository.get_by_id(
            db=db,
            campaign_id=campaign_id,
            business_id=business_id
        )

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        content = CampaignContentRepository.get_by_id(
            db=db,
            content_id=content_id,
            campaign_id=campaign_id
        )

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign content not found"
            )

        return CampaignContentRepository.update(
            db=db,
            db_content=content,
            content_data=content_data
        )

    @staticmethod
    def delete_content(
        db: Session,
        content_id: int,
        campaign_id: int,
        business_id: int
    ):

        campaign = CampaignRepository.get_by_id(
            db=db,
            campaign_id=campaign_id,
            business_id=business_id
        )

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

        content = CampaignContentRepository.get_by_id(
            db=db,
            content_id=content_id,
            campaign_id=campaign_id
        )

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign content not found"
            )

        CampaignContentRepository.delete(
            db=db,
            db_content=content
        )

        return {
            "message": "Campaign content deleted successfully"
        }