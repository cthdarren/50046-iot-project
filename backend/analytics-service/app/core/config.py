from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    AVAILABILITY_SERVICE_URL: str
    AVAILABILITY_SERVICE_PORT: int

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()
