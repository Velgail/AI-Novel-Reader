import requests
from core.config import config
from core.logger_setup import setup_logger

logger = setup_logger()

class LLMClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.base_url = "https://api.gemini.com/v1"
        if not self.api_key:
            logger.warning("API key is not set. LLMClient will not function properly.")

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_text(self, prompt, max_tokens=100):
        url = f"{self.base_url}/generate"
        headers = self._get_headers()
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("text", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate text: {e}")
            return ""

    def get_model_info(self):
        url = f"{self.base_url}/models"
        headers = self._get_headers()

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get model info: {e}")
            return {}
