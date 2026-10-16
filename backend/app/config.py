from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "InvenTrack API"
    database_url: str = "postgresql+psycopg://inventrack:inventrack@localhost:5432/inventrack"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
