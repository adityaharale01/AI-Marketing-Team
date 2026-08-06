from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    product_name: str
    category: str
    price: float
    stock: int


class ProductResponse(BaseModel):
    id: int
    product_name: str
    category: str
    price: float
    stock: int

    model_config = ConfigDict(from_attributes=True)