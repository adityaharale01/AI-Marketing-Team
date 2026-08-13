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

from app.schemas.ai_interactions import (
    AIInteractionCreate,
    AIInteractionResponse
)

from app.services.ai_interaction_service import (
    AIInteractionService
)


router = APIRouter(
    prefix="/ai-interactions",
    tags=["AI Interactions"]
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
    response_model=AIInteractionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_interaction(
    interaction: AIInteractionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(current_user)

    return AIInteractionService.create_interaction(
        db=db,
        user_id=current_user.id,
        business_id=business.id,
        interaction_data=interaction
    )


@router.get(
    "/",
    response_model=list[AIInteractionResponse]
)
def get_interactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(current_user)

    return AIInteractionService.get_interactions(
        db=db,
        business_id=business.id
    )


@router.get(
    "/agent/{agent_type}",
    response_model=list[AIInteractionResponse]
)
def get_agent_interactions(
    agent_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(current_user)

    return AIInteractionService.get_agent_interactions(
        db=db,
        business_id=business.id,
        agent_type=agent_type
    )


@router.get(
    "/{interaction_id}",
    response_model=AIInteractionResponse
)
def get_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(current_user)

    return AIInteractionService.get_interaction(
        db=db,
        interaction_id=interaction_id,
        business_id=business.id
    )


@router.delete(
    "/{interaction_id}"
)
def delete_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    business = get_user_business(current_user)

    return AIInteractionService.delete_interaction(
        db=db,
        interaction_id=interaction_id,
        business_id=business.id
    )