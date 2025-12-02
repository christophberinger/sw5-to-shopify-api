from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from api.routes import shopware, shopify, mapping, customers, orders, articles

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting SW5 to Shopify Import Tool...")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="SW5 to Shopify Import Tool",
    description="Import products, customers, and orders from Shopware 5 (including Pickware fields) to Shopify with flexible field mapping",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(shopware.router, prefix="/api/shopware", tags=["Shopware 5"])
app.include_router(shopify.router, prefix="/api/shopify", tags=["Shopify"])
app.include_router(mapping.router, prefix="/api/mapping", tags=["Mapping"])
app.include_router(articles.router, prefix="/api/articles", tags=["Articles"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])


@app.get("/")
async def root():
    return {
        "message": "SW5 to Shopify Import Tool API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
