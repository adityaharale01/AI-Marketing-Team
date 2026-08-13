from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CampaignContent(Base):
    __tablename__ = "campaign_contents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    campaign_id = Column(
        Integer,
        ForeignKey(
            "campaigns.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    content_type = Column(
        String(50),
        nullable=False
    )

    platform = Column(
        String(50),
        nullable=False
    )

    content_text = Column(
        Text,
        nullable=False
    )

    created_by_ai = Column(
        Boolean,
        nullable=False,
        default=True
    )

    is_approved = Column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    campaign = relationship(
        "Campaign",
        back_populates="contents"
    )