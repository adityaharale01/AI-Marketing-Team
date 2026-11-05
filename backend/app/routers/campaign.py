from fastapi import (
    APIRouter,
    Depends,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_active_business
from app.models.business import Business

from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse
)

from app.services.campaign_service import (
    CampaignService
)


router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)


@router.post(
    "/",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED
)
def create_campaign(
    campaign: CampaignCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignService.create_campaign(
        db=db,
        business_id=business.id,
        campaign_data=campaign
    )


@router.get(
    "/",
    response_model=list[CampaignResponse]
)
def get_campaigns(
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignService.get_campaigns(
        db=db,
        business_id=business.id
    )


@router.get(
    "/search",
    response_model=list[CampaignResponse]
)
def search_campaigns(
    name: str,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignService.search_campaigns(
        db=db,
        business_id=business.id,
        name=name
    )


@router.get(
    "/status/{campaign_status}",
    response_model=list[CampaignResponse]
)
def get_campaigns_by_status(
    campaign_status: str,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignService.get_campaigns_by_status(
        db=db,
        business_id=business.id,
        campaign_status=campaign_status
    )


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse
)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignService.get_campaign(
        db=db,
        campaign_id=campaign_id,
        business_id=business.id
    )


@router.put(
    "/{campaign_id}",
    response_model=CampaignResponse
)
def update_campaign(
    campaign_id: int,
    campaign: CampaignUpdate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignService.update_campaign(
        db=db,
        campaign_id=campaign_id,
        business_id=business.id,
        campaign_data=campaign
    )


@router.delete(
    "/{campaign_id}"
)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignService.delete_campaign(
        db=db,
        campaign_id=campaign_id,
        business_id=business.id
    )