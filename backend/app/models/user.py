from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)

    email = Column(String(150), unique=True, nullable=False)

    password = Column(String(255), nullable=False)

    role = Column(String(30), default="owner")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    businesses = relationship("Business", back_populates="owner")