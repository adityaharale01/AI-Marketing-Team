from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    business_name = Column(String(100), nullable=False)

    business_type = Column(String(50), nullable=False)

    description = Column(Text)

    email = Column(String(100), unique=True)

    phone = Column(String(20))

    website = Column(String(255))

    address = Column(String(255))

    city = Column(String(100))

    state = Column(String(100))

    country = Column(String(100))

    pincode = Column(String(10))

    logo = Column(String(255))

    gst_number = Column(String(20))

    business_registration_number = Column(String(50))

    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    owner = relationship(
        "User",
        back_populates="businesses"
    )

    products = relationship(
        "Product",
        back_populates="business",
        cascade="all, delete"
    )

    sales = relationship(
    "Sale",
    back_populates="business",
    cascade="all, delete-orphan"
)