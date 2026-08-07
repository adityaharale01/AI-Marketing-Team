from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    product_name = Column(String(100), nullable=False)

    category = Column(String(100))

    price = Column(Float, nullable=False)

    stock = Column(Integer, default=0)
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False
    )

    business = relationship(
        "Business",
        back_populates="products"
    )