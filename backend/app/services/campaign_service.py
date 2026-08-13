from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.campaign_repository import (
    CampaignRepository
)

from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate
)


ALLOWED_STATUSES = {
    "draft",
    "scheduled",
    "active",
    "completed",
    "cancelled"
}


class CampaignService:

    @staticmethod
    def create_campaign(
        db: Session,
        business_id: int,
        campaign_data: CampaignCreate
    ):

        return CampaignRepository.create(
            db=db,
            business_id=business_id,
            campaign_data=campaign_data
        )

    @staticmethod
    def get_campaigns(
        db: Session,
        business_id: int
    ):

        return CampaignRepository.get_all(
            db=db,
            business_id=business_id
        )

    @staticmethod
    def get_campaign(
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

        return campaign

    @staticmethod
    def get_campaigns_by_status(
        db: Session,
        business_id: int,
        campaign_status: str
    ):

        if campaign_status not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid campaign status"
            )

        return CampaignRepository.get_by_status(
            db=db,
            business_id=business_id,
            status=campaign_status
        )

    @staticmethod
    def search_campaigns(
        db: Session,
        business_id: int,
        name: str
    ):

        return CampaignRepository.search(
            db=db,
            business_id=business_id,
            name=name
        )

    @staticmethod
    def update_campaign(
        db: Session,
        campaign_id: int,
        business_id: int,
        campaign_data: CampaignUpdate
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

        update_data = campaign_data.model_dump(
            exclude_unset=True
        )

        start_date = update_data.get(
            "start_date",
            campaign.start_date
        )

        end_date = update_data.get(
            "end_date",
            campaign.end_date
        )

        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date cannot be before start date"
            )

        return CampaignRepository.update(
            db=db,
            db_campaign=campaign,
            campaign_data=campaign_data
        )

    @staticmethod
    def delete_campaign(
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

        CampaignRepository.delete(
            db=db,
            db_campaign=campaign
        )

        return {
            "message": "Campaign deleted successfully"
        }