from fastapi import (
    APIRouter,
    Depends,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.oauth2 import get_current_user
from app.dependencies import get_active_business
from app.models.business import Business

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


@router.post(
    "/",
    response_model=AIInteractionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_interaction(
    interaction: AIInteractionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    business: Business = Depends(get_active_business)
):

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
    business: Business = Depends(get_active_business)
):

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
    business: Business = Depends(get_active_business)
):

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
    business: Business = Depends(get_active_business)
):

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
    business: Business = Depends(get_active_business)
):

    return AIInteractionService.delete_interaction(
        db=db,
        interaction_id=interaction_id,
        business_id=business.id
    )