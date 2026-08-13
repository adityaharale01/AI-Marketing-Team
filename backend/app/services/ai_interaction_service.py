from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.ai_interaction_repository import (
    AIInteractionRepository
)

from app.schemas.ai_interactions import (
    AIInteractionCreate
)


ALLOWED_AGENTS = {
    "business_intelligence",
    "marketing_strategy",
    "content_generation",
    "sales_forecasting",
    "recommendation"
}


class AIInteractionService:

    @staticmethod
    def create_interaction(
        db: Session,
        user_id: int,
        business_id: int,
        interaction_data: AIInteractionCreate
    ):

        if interaction_data.agent_type not in ALLOWED_AGENTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid agent type"
            )

        return AIInteractionRepository.create(
            db=db,
            user_id=user_id,
            business_id=business_id,
            interaction_data=interaction_data
        )

    @staticmethod
    def get_interactions(
        db: Session,
        business_id: int
    ):

        return AIInteractionRepository.get_all(
            db=db,
            business_id=business_id
        )

    @staticmethod
    def get_interaction(
        db: Session,
        interaction_id: int,
        business_id: int
    ):

        interaction = (
            AIInteractionRepository.get_by_id(
                db=db,
                interaction_id=interaction_id,
                business_id=business_id
            )
        )

        if not interaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI interaction not found"
            )

        return interaction

    @staticmethod
    def get_agent_interactions(
        db: Session,
        business_id: int,
        agent_type: str
    ):

        if agent_type not in ALLOWED_AGENTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid agent type"
            )

        return AIInteractionRepository.get_by_agent(
            db=db,
            business_id=business_id,
            agent_type=agent_type
        )

    @staticmethod
    def delete_interaction(
        db: Session,
        interaction_id: int,
        business_id: int
    ):

        interaction = (
            AIInteractionRepository.get_by_id(
                db=db,
                interaction_id=interaction_id,
                business_id=business_id
            )
        )

        if not interaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI interaction not found"
            )

        AIInteractionRepository.delete(
            db=db,
            interaction=interaction
        )

        return {
            "message": "AI interaction deleted successfully"
        }