import os
from dotenv import load_dotenv
from core.logger_setup import setup_logger

logger = setup_logger()

load_dotenv()


class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/novel_context.db")

    def __init__(self):
        missing = []
        if not self.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not self.DATABASE_URL:
            missing.append("DATABASE_URL")
        if missing:
            logger.warning(
                f"The following environment variables are not set: {', '.join(missing)}. Please set them in your environment or .env file.")
        logger.info(f"Database URL set to: {self.DATABASE_URL}")


config = Config()
