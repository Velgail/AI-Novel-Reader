import os
from dotenv import load_dotenv
from core.logger_setup import setup_logger

logger = setup_logger()

load_dotenv()


class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/novel_context.db")

    def __init__(self):
        if not self.GEMINI_API_KEY:
            logger.warning(
                "GEMINI_API_KEY is not set in environment variables or .env file.")
        logger.info(f"Database URL set to: {self.DATABASE_URL}")


config = Config()
