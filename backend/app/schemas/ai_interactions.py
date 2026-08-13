from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


class AIInteractionBase(BaseModel):

    agent_type: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    user_query: str = Field(
        ...,
        min_length=1,
        max_length=10000
    )

    ai_response: str = Field(
        ...,
        min_length=1,
        max_length=20000
    )


class AIInteractionCreate(AIInteractionBase):
    pass


class AIInteractionResponse(AIInteractionBase):

    id: int

    user_id: int

    business_id: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )