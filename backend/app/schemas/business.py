from pydantic import BaseModel, ConfigDict


class BusinessCreate(BaseModel):
    business_name: str
    business_type: str
    description: str | None = None
    phone: str | None = None
    address: str | None = None


class BusinessResponse(BaseModel):
    id: int
    business_name: str
    business_type: str
    description: str | None
    phone: str | None
    address: str | None

    model_config = ConfigDict(from_attributes=True)