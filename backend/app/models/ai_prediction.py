from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

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

    product_id = Column(
        Integer,
        ForeignKey(
            "products.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    prediction_type = Column(
        String(50),
        nullable=False
    )

    predicted_value = Column(
        Float,
        nullable=False
    )

    prediction_date = Column(
        Date,
        nullable=False
    )

    period = Column(
        String(50),
        nullable=False
    )

    model_name = Column(
        String(100),
        nullable=False
    )

    confidence_score = Column(
        Float,
        nullable=True
    )

    explanation = Column(
        Text,
        nullable=True
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
        back_populates="ai_predictions"
    )

    product = relationship(
        "Product",
        back_populates="ai_predictions"
    )