from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017/"
    database_name: str = "ecommerce"

    class Config:
        env_file = ".env" # You can use a .env file for sensitive info

settings = Settings()