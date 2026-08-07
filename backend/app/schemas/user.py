from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


# Request Schema
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


# Login Schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Response Schema
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str