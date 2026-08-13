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
    "/{campaign_id}/contents",
    response_model=CampaignContentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_content(
    campaign_id: int,
    content: CampaignContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

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
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

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
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

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
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

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
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

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
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(
        current_user
    )

    return CampaignContentService.delete_content(
        db=db,
        content_id=content_id,
        campaign_id=campaign_id,
        business_id=business.id
    )