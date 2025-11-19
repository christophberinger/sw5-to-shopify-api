from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Shopware 5
    sw5_api_url: str
    sw5_api_username: str
    sw5_api_key: str

    # Shopify
    shopify_shop_url: str
    shopify_access_token: str
    shopify_api_version: str = "2024-01"

    # CORS
    allowed_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
