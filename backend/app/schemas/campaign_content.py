from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


class CampaignContentBase(BaseModel):

    content_type: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    platform: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    content_text: str = Field(
        ...,
        min_length=1,
        max_length=10000
    )

    created_by_ai: bool = True

    is_approved: bool = False


class CampaignContentCreate(
    CampaignContentBase
):
    pass


class CampaignContentUpdate(BaseModel):

    content_type: str | None = Field(
        default=None,
        min_length=2,
        max_length=50
    )

    platform: str | None = Field(
        default=None,
        min_length=2,
        max_length=50
    )

    content_text: str | None = Field(
        default=None,
        min_length=1,
        max_length=10000
    )

    is_approved: bool | None = None


class CampaignContentResponse(
    CampaignContentBase
):

    id: int

    campaign_id: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )