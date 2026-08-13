from decimal import Decimal
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
        max_length=50
    )

    description: str | None = Field(
        default=None,
        max_length=500
    )

    sku: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2
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
        max_length=50
    )

    description: str | None = Field(
        default=None,
        max_length=500
    )

    sku: str | None = Field(
        default=None,
        min_length=2,
        max_length=50
    )

    price: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2
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