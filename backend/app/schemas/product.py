from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):

    product_name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    category: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    description: str | None = Field(
        default=None,
        max_length=1000
    )

    sku: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    price: float = Field(
        ...,
        gt=0
    )

    stock: int = Field(
        default=0,
        ge=0
    )

    image_url: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):

    product_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    category: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    description: str | None = Field(
        default=None,
        max_length=1000
    )

    sku: str | None = Field(
        default=None,
        min_length=2,
        max_length=50
    )

    price: float | None = Field(
        default=None,
        gt=0
    )

    stock: int | None = Field(
        default=None,
        ge=0
    )

    image_url: str | None = None

    is_active: bool | None = None


class ProductResponse(ProductBase):

    id: int
    business_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )