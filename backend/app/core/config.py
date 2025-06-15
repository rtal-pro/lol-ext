import os
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "League of Legends Extension API"
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Environment
    DEBUG: bool = False
    ENV: str = "production"  # development, staging, production
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    DATABASE_URL: Optional[str] = None
    
    # Riot API
    RIOT_API_KEY: str = ""
    RIOT_API_BASE_URL: str = "https://euw1.api.riotgames.com"
    
    # Data Dragon
    DATA_DRAGON_BASE_URL: str = "https://ddragon.leagueoflegends.com"
    DATA_DRAGON_CDN: str = "https://ddragon.leagueoflegends.com/cdn"
    ENABLE_SCHEDULED_TASKS: bool = True
    DATA_SYNC_INTERVAL_HOURS: int = 24
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'Settings':
        if not self.DATABASE_URL:
            self.DATABASE_URL = PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=f"{self.POSTGRES_DB}"
            ).unicode_string()
        return self
    
    class Config:
        case_sensitive = True
        env_file = ".env"


# Load settings based on environment
def get_settings() -> Settings:
    env = os.getenv("ENV", "development")
    env_file = f".env.{env}" if env != "production" else ".env"
    
    return Settings(_env_file=env_file)


settings = get_settings()