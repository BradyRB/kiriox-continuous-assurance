from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://kiriox:kiriox@127.0.0.1:5432/kiriox"
    kiriox_master_key: str = "dev-only-change-me-32-bytes-minimum"
    kiriox_default_timezone: str = "America/Santo_Domingo"
    kiriox_batch_size: int = 5000
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
