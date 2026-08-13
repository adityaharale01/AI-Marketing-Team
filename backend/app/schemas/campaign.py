from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator
)


class CampaignBase(BaseModel):

    campaign_name: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    objective: str = Field(
        ...,
        min_length=2,
        max_length=255
    )

    target_audience: str | None = Field(
        default=None,
        max_length=1000
    )

    platform: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    start_date: date

    end_date: date

    budget: float | None = Field(
        default=None,
        ge=0
    )

    status: str = Field(
        default="draft",
        pattern="^(draft|scheduled|active|completed|cancelled)$"
    )


class CampaignCreate(CampaignBase):

    @model_validator(mode="after")
    def validate_dates(self):

        if self.end_date < self.start_date:
            raise ValueError(
                "End date cannot be before start date"
            )

        return self


class CampaignUpdate(BaseModel):

    campaign_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    objective: str | None = Field(
        default=None,
        min_length=2,
        max_length=255
    )

    target_audience: str | None = Field(
        default=None,
        max_length=1000
    )

    platform: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    start_date: date | None = None

    end_date: date | None = None

    budget: float | None = Field(
        default=None,
        ge=0
    )

    status: str | None = Field(
        default=None,
        pattern="^(draft|scheduled|active|completed|cancelled)$"
    )

    is_active: bool | None = None


class CampaignResponse(CampaignBase):

    id: int

    business_id: int

    is_active: bool

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )