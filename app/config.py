
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "SaaS Condomínio Inovador"
    PROJECT_VERSION: str = "1.0.0"
    
    # Puxa a URL do banco do arquivo .env
    DATABASE_URL: str = os.getenv("DATABASE_URL")

settings = Settings()