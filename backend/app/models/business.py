from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)

    business_name = Column(String(100), nullable=False)

    business_type = Column(String(50), nullable=False)

    description = Column(String(255))

    phone = Column(String(20))

    address = Column(String(255))

    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="businesses")

    products = relationship("Product", back_populates="business")