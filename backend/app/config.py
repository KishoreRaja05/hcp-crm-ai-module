import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "gemma2-9b-it")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hcp_crm"
)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
