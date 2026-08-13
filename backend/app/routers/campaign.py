from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.oauth2 import get_current_user

from app.models.user import User

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


def get_user_business(
    current_user: User
):

    if not current_user.businesses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a business"
        )

    return current_user.businesses[0]


@router.post(
    "/",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED
)
def create_campaign(
    campaign: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

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
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

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
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

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
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

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
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

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
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

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
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

    return CampaignService.delete_campaign(
        db=db,
        campaign_id=campaign_id,
        business_id=business.id
    )