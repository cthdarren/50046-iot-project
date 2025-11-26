from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()