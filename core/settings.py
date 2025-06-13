from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # SQLite settings
    DATABASE_URL: str = "sqlite:///user.db"
    SECRET_KEY: str = "secret-key-111"
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./user.db"  

    # JWT settings
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRES_DAYS: int = 30
    EXPIRES_DELTA: int = 15

    # MongoDB settings
    MONGODB_URL: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DB_NAME: str = "website_with_recepies"
    MONGODB_COLLECTION_RECIPES: str = "recepies"
    


    class Config:
        env_file = Path(__file__).parent.parent / ".env"


settings = Settings()
