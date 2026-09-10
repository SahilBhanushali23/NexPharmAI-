from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "NexPharmAI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # JWT & Security
    JWT_SECRET: str = "nexpharm_enterprise_super_secret_jwt_key_2026_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # Database
    DATABASE_URL: str = "sqlite:///./nexpharm.db"
    
    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def resolve_sqlite_path(cls, v: str) -> str:
        if v.startswith("sqlite:///") and not v.startswith("sqlite:////"):
            rel_path = v.replace("sqlite:///", "")
            if rel_path.startswith("./"):
                rel_path = rel_path[2:]
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            abs_db_path = os.path.join(backend_dir, rel_path).replace("\\", "/")
            return f"sqlite:///{abs_db_path}"
        return v
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
        
    # ML & Storage
    MODEL_PATH: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ml/models"))

    @field_validator("MODEL_PATH", mode="after")
    @classmethod
    def resolve_model_path(cls, v: str) -> str:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        candidate = os.path.abspath(os.path.join(root_dir, "ml/models"))
        if os.path.exists(candidate):
            return candidate
        if not os.path.isabs(v):
            return os.path.abspath(os.path.join(root_dir, v))
        return v

    
    # AI Decision Assistant
    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-pro"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

settings = Settings()
