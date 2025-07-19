from pydantic import BaseModel, Field
from typing import List, Optional

class ProductSize(BaseModel):
    size: str
    quantity: int

class ProductIn(BaseModel):
    name: str
    price: float
    sizes: List[ProductSize] = []

class ProductOut(BaseModel):
    id: str = Field(alias="_id")
    name: str
    price: float

    class Config:
        populate_by_name = True # Allows mapping _id to id