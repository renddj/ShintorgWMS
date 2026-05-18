import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://shintorg:shintorg@db:5432/shintorg_wms")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-very-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
