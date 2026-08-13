from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    business_id = Column(
        Integer,
        ForeignKey(
            "businesses.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    campaign_name = Column(
        String(150),
        nullable=False
    )

    objective = Column(
        String(255),
        nullable=False
    )

    target_audience = Column(
        Text,
        nullable=True
    )

    platform = Column(
        String(100),
        nullable=False
    )

    start_date = Column(
        Date,
        nullable=False
    )

    end_date = Column(
        Date,
        nullable=False
    )

    budget = Column(
        Float,
        nullable=True
    )

    status = Column(
        String(30),
        nullable=False,
        default="draft"
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
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

    business = relationship(
        "Business",
        back_populates="campaigns"
    )
    contents = relationship(
    "CampaignContent",
    back_populates="campaign",
    cascade="all, delete-orphan"
)