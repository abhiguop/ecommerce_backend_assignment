from fastapi import FastAPI
from routers import products, orders # Ensure both 'products' and 'orders' are imported

app = FastAPI(
    title="E-commerce Backend API",
    description="A sample e-commerce backend built with FastAPI and MongoDB."
)

# Include the routers with their respective prefixes
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1") # <-- This line is crucial for /orders endpoints

@app.get("/")
async def root():
    return {"message": "Welcome to the E-commerce Backend API!"}