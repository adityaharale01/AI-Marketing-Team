from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)

    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False)

    unit_price = Column(Numeric(10, 2), nullable=False)

    total_amount = Column(Numeric(12, 2), nullable=False)

    sale_date = Column(
        DateTime(timezone=True),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    business = relationship(
        "Business",
        back_populates="sales"
    )

    product = relationship(
        "Product",
        back_populates="sales"
    )