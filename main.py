from core.logger_setup import setup_logger
from core.config import config

logger = setup_logger()

def main():
    logger.info("Novel LLM Project - Main Application Started")
    logger.info(f"Gemini API Key Loaded: {'Yes' if config.GEMINI_API_KEY else 'No'}")
    print("Hello, Novel LLM Project!")

if __name__ == "__main__":
    main()
