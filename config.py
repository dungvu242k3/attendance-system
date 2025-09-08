import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change_me")

    DB_NAME = os.getenv("DB_NAME", "face_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "sat24042003")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))

    MODEL_PATH = os.getenv("MODEL_PATH", "./models/best_model.pth")

    CHECKIN_HOUR = int(os.getenv("CHECKIN_HOUR", 9)) 
    CHECKOUT_HOUR = int(os.getenv("CHECKOUT_HOUR", 18))  

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    
"""    if os.path.exists("/.dockerenv"):
        DB_HOST = os.getenv("DB_HOST", "db")
    else:
        DB_HOST = os.getenv("DB_HOST", "localhost")"""
