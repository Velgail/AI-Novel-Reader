import os
from dotenv import load_dotenv
from core.logger_setup import setup_logger

logger = setup_logger()

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    def __init__(self):
        if not self.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set in environment variables or .env file.")

config = Config()
