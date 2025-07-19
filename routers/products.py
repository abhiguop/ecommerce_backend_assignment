from fastapi import APIRouter, HTTPException, Depends, Query
from pymongo.collection import Collection
from typing import List, Optional
from bson import ObjectId # <--- Ensure this import is present at the top
from models.product import ProductIn, ProductOut
from database import get_database

router = APIRouter()

@router.post("/products", response_model=dict, status_code=201)
async def create_product(product: ProductIn, db: Collection = Depends(get_database)):
    products_collection = db["products"]
    product_dict = product.model_dump(by_alias=True)
    result = products_collection.insert_one(product_dict)
    return {"id": str(result.inserted_id)}

@router.get("/products", response_model=dict, status_code=200)
async def list_products(
    name: Optional[str] = Query(None, description="Partial search for product name"),
    size: Optional[str] = Query(None, description="Filter by product size"),
    limit: int = Query(0, ge=0, description="Number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip for pagination"),
    db: Collection = Depends(get_database)
):
    products_collection = db["products"]
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"} # Case-insensitive partial match
    if size:
        query["sizes.size"] = size # Query for size within the sizes array

    total_records = products_collection.count_documents(query)
    
    products_cursor = products_collection.find(query).sort("_id").skip(offset)
    if limit > 0:
        products_cursor = products_cursor.limit(limit)

    products_data = []
    for product_doc in products_cursor:
        # --- START OF CHANGE ---
        # Convert MongoDB ObjectId to string for Pydantic validation
        if "_id" in product_doc and isinstance(product_doc["_id"], ObjectId):
            product_doc["_id"] = str(product_doc["_id"])
        # --- END OF CHANGE ---

        # Remove sizes from the output as per the spec for List Products API
        product_doc.pop("sizes", None)
        products_data.append(ProductOut(**product_doc).model_dump(by_alias=True))

    next_offset = offset + len(products_data) if len(products_data) > 0 else 0
    previous_offset = max(0, offset - limit) if limit > 0 else -10 # Using -10 as per spec example

    return {
        "data": products_data,
        "page": {
            "next": next_offset,
            "limit": limit,
            "previous": previous_offset
        }
    }