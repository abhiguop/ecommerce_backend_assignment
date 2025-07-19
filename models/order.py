from pydantic import BaseModel, Field
from typing import List, Optional

class OrderItemIn(BaseModel):
    productId: str
    qty: int

class OrderItemOut(BaseModel):
    productDetails: dict # This will be populated from product collection
    qty: int

class OrderIn(BaseModel):
    userId: str 
    items: List[OrderItemIn]

class OrderOut(BaseModel):
    id: str = Field(alias="_id")
    items: List[OrderItemOut]
    total: float = 0.0 

    class Config:
        populate_by_name = True