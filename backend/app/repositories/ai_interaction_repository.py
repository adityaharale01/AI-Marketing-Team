from sqlalchemy.orm import Session

from app.models.ai_interaction import AIInteraction
from app.schemas.ai_interactions import AIInteractionCreate


class AIInteractionRepository:

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        business_id: int,
        interaction_data: AIInteractionCreate
    ):

        db_interaction = AIInteraction(
            user_id=user_id,
            business_id=business_id,
            **interaction_data.model_dump()
        )

        db.add(db_interaction)
        db.commit()
        db.refresh(db_interaction)

        return db_interaction

    @staticmethod
    def get_all(
        db: Session,
        business_id: int
    ):

        return (
            db.query(AIInteraction)
            .filter(
                AIInteraction.business_id == business_id
            )
            .order_by(
                AIInteraction.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        interaction_id: int,
        business_id: int
    ):

        return (
            db.query(AIInteraction)
            .filter(
                AIInteraction.id == interaction_id,
                AIInteraction.business_id == business_id
            )
            .first()
        )

    @staticmethod
    def get_by_agent(
        db: Session,
        business_id: int,
        agent_type: str
    ):

        return (
            db.query(AIInteraction)
            .filter(
                AIInteraction.business_id == business_id,
                AIInteraction.agent_type == agent_type
            )
            .order_by(
                AIInteraction.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def delete(
        db: Session,
        interaction: AIInteraction
    ):

        db.delete(interaction)
        db.commit()