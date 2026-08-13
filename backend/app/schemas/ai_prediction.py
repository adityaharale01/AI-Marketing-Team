from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


class AIPredictionBase(BaseModel):

    product_id: int

    prediction_type: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    predicted_value: float = Field(
        ...,
        ge=0
    )

    prediction_date: date

    period: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    model_name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    confidence_score: float | None = Field(
        default=None,
        ge=0,
        le=1
    )

    explanation: str | None = Field(
        default=None,
        max_length=5000
    )


class AIPredictionCreate(AIPredictionBase):
    pass


class AIPredictionResponse(AIPredictionBase):

    id: int

    business_id: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )