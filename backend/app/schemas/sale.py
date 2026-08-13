from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from decimal import Decimal


class SaleBase(BaseModel):
    product_id: int

    quantity: int = Field(
        ...,
        gt=0,
        description="Number of units sold"
    )

    unit_price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2
    )

    sale_date: datetime


class SaleCreate(SaleBase):
    pass


class SaleUpdate(BaseModel):
    product_id: int | None = None

    quantity: int | None = Field(
        default=None,
        gt=0
    )

    unit_price: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2
    )

    sale_date: datetime | None = None


class SaleResponse(SaleBase):
    id: int
    business_id: int
    total_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )