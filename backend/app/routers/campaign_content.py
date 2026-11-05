from fastapi import (
    APIRouter,
    Depends,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_active_business
from app.models.business import Business

from app.schemas.campaign_content import (
    CampaignContentCreate,
    CampaignContentUpdate,
    CampaignContentResponse
)

from app.services.campaign_content_service import (
    CampaignContentService
)


router = APIRouter(
    prefix="/campaigns",
    tags=["Campaign Content"]
)


@router.post(
    "/{campaign_id}/contents",
    response_model=CampaignContentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_content(
    campaign_id: int,
    content: CampaignContentCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignContentService.create_content(
        db=db,
        campaign_id=campaign_id,
        business_id=business.id,
        content_data=content
    )


@router.get(
    "/{campaign_id}/contents",
    response_model=list[CampaignContentResponse]
)
def get_contents(
    campaign_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignContentService.get_contents(
        db=db,
        campaign_id=campaign_id,
        business_id=business.id
    )


@router.get(
    "/{campaign_id}/contents/type/{content_type}",
    response_model=list[CampaignContentResponse]
)
def get_content_by_type(
    campaign_id: int,
    content_type: str,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignContentService.get_by_type(
        db=db,
        campaign_id=campaign_id,
        business_id=business.id,
        content_type=content_type
    )


@router.get(
    "/{campaign_id}/contents/{content_id}",
    response_model=CampaignContentResponse
)
def get_content(
    campaign_id: int,
    content_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignContentService.get_content(
        db=db,
        content_id=content_id,
        campaign_id=campaign_id,
        business_id=business.id
    )


@router.put(
    "/{campaign_id}/contents/{content_id}",
    response_model=CampaignContentResponse
)
def update_content(
    campaign_id: int,
    content_id: int,
    content: CampaignContentUpdate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignContentService.update_content(
        db=db,
        content_id=content_id,
        campaign_id=campaign_id,
        business_id=business.id,
        content_data=content
    )


@router.delete(
    "/{campaign_id}/contents/{content_id}"
)
def delete_content(
    campaign_id: int,
    content_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_active_business)
):

    return CampaignContentService.delete_content(
        db=db,
        content_id=content_id,
        campaign_id=campaign_id,
        business_id=business.id
    )