from fastapi import APIRouter, HTTPException, Depends, Query
from pymongo.collection import Collection
from typing import List, Optional
from bson import ObjectId # Needed for converting string IDs to MongoDB ObjectIds
from models.order import OrderIn, OrderOut, OrderItemOut
from models.product import ProductOut # Used for type hinting or if you needed to validate product output structure
from database import get_database

router = APIRouter() # This line initializes the router for order-related routes

@router.post("/orders", response_model=dict, status_code=201)
async def create_order(order: OrderIn, db: Collection = Depends(get_database)):
    orders_collection = db["orders"]
    products_collection = db["products"]

    order_items_details = []
    total_price = 0.0

    for item in order.items:
        # Crucial: Convert the string productId from the request body to MongoDB's ObjectId
        try:
            product_object_id = ObjectId(item.productId)
        except Exception: # Catching a general exception for InvalidId, or specifically bson.errors.InvalidId
            raise HTTPException(status_code=400, detail=f"Invalid product ID format: {item.productId}")

        product_doc = products_collection.find_one({"_id": product_object_id})
        
        if not product_doc:
            raise HTTPException(status_code=404, detail=f"Product with ID {item.productId} not found.")

        # Get product name and price for embedding in the order
        product_name = product_doc.get("name")
        product_price = product_doc.get("price")

        if "sizes" in product_doc and product_doc["sizes"]: # Check if sizes exist and are not empty
            size_found = False
            for size_info in product_doc["sizes"]:
                if size_info["quantity"] >= item.qty:
                    size_info["quantity"] -= item.qty
                    products_collection.update_one(
                        {"_id": product_object_id, "sizes.size": size_info["size"]},
                        {"$set": {"sizes.$.quantity": size_info["quantity"]}}
                    )
                    size_found = True
                    break
            if not size_found:
                raise HTTPException(status_code=400, detail=f"Not enough stock for product '{product_name}' (ID: {item.productId}).")
        else: 
            pass


        order_items_details.append({
            "productDetails": {
                "name": product_name,
                "id": str(product_doc["_id"]) # Store as string for consistency with output
            },
            "qty": item.qty
        })
        total_price += product_price * item.qty

    order_dict = order.model_dump(by_alias=True)
    order_dict["items"] = order_items_details
    order_dict["total"] = total_price
    result = orders_collection.insert_one(order_dict)
    
    return {"id": str(result.inserted_id)}


@router.get("/orders/{user_id}", response_model=dict, status_code=200)
async def get_orders_for_user(
    user_id: str,
    limit: int = Query(0, ge=0, description="Number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip for pagination"),
    db: Collection = Depends(get_database)
):
    orders_collection = db["orders"]
    
    query = {"userId": user_id}

    total_records = orders_collection.count_documents(query) # Total records for pagination info

    orders_cursor = orders_collection.find(query).sort("_id").skip(offset)
    if limit > 0:
        orders_cursor = orders_cursor.limit(limit)

    orders_data = []
    for order_doc in orders_cursor:
        # Convert ObjectId to string for the order's _id
        if "_id" in order_doc and isinstance(order_doc["_id"], ObjectId):
            order_doc["_id"] = str(order_doc["_id"])
        
        # Ensure productDetails.id is also a string if it somehow remains ObjectId
        for item in order_doc.get("items", []):
            if "productDetails" in item and "id" in item["productDetails"]:
                if isinstance(item["productDetails"]["id"], ObjectId):
                    item["productDetails"]["id"] = str(item["productDetails"]["id"])

        orders_data.append(OrderOut(**order_doc).model_dump(by_alias=True))

    next_offset = offset + len(orders_data) if len(orders_data) > 0 else 0
    previous_offset = max(0, offset - limit) if limit > 0 else -10 

    return {
        "data": orders_data,
        "page": {
            "next": next_offset,
            "limit": limit,
            "previous": previous_offset,
            "total": total_records # Adding total records for clarity in pagination
        }
    }