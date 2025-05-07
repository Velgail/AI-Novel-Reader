# core/llm_client.py (修正案)
import google.generativeai as genai
from core.config import config
from core.logger_setup import setup_logger

logger = setup_logger()

class LLMClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model = None
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. LLMClient will not function properly.")
        else:
            try:
                genai.configure(api_key=self.api_key)
                # TODO: モデル名は設定ファイル等で指定できるようにすることを推奨
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("LLMClient initialized with gemini-pro model.")
            except Exception as e:
                logger.error(f"Failed to configure Gemini API: {e}")


    def generate_text(self, prompt_text, **generation_kwargs):
        if not self.model:
            logger.error("LLM model not initialized. Cannot generate text.")
            return ""
        try:
            # generation_kwargs は temperature, top_p, top_k, max_output_tokens など
            response = self.model.generate_content(prompt_text, generation_config=genai.types.GenerationConfig(**generation_kwargs))
            # エラーハンドリングやブロックされた場合の処理を追加することを推奨
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                logger.warning(f"Prompt was blocked: {response.prompt_feedback.block_reason}")
                return f"Error: Prompt blocked ({response.prompt_feedback.block_reason})"
            if not response.candidates:
                 logger.warning("No candidates returned from LLM.")
                 return "Error: No response from LLM."
            return response.text
        except Exception as e:
            logger.error(f"Failed to generate text using Gemini API: {e}")
            return f"Error: Failed to generate text ({e})"

    def get_model_info(self):
        if not self.model:
            logger.error("LLM model not initialized.")
            return {}
        try:
            # 利用可能なモデルのリストを取得する例 (必要に応じて)
            # available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            return {
                "configured_model_name": self.model.model_name if self.model else "N/A",
                # "available_models": available_models
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}