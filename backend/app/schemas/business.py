from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class BusinessBase(BaseModel):
    business_name: str
    business_type: str
    description: Optional[str] = None

    email: EmailStr

    phone: str

    website: Optional[str] = None

    address: str

    city: str

    state: str

    country: str

    pincode: str

    logo: Optional[str] = None

    gst_number: Optional[str] = None

    business_registration_number: Optional[str] = None


class BusinessCreate(BusinessBase):
    pass


class BusinessUpdate(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    description: Optional[str] = None

    email: Optional[EmailStr] = None

    phone: Optional[str] = None

    website: Optional[str] = None

    address: Optional[str] = None

    city: Optional[str] = None

    state: Optional[str] = None

    country: Optional[str] = None

    pincode: Optional[str] = None

    logo: Optional[str] = None

    gst_number: Optional[str] = None

    business_registration_number: Optional[str] = None

    is_active: Optional[bool] = None


class BusinessResponse(BusinessBase):
    id: int

    owner_id: int

    is_active: bool

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)