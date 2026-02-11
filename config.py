from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "retirement_goal_db"
    DB_USER: str = "retirement_app"
    DB_PASSWORD: str = "mannlowe@16"
    
    # Application
    APP_NAME: str = "Retirement Goal API"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"

    # Groq LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    GROQ_TIMEOUT_S: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
