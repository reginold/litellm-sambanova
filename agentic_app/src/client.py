"""SambaNova API client."""

import os
import logging
import requests
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SambaNovaClient:
    """Client for interacting with SambaNova API."""
    
    DEFAULT_BASE_URL = "https://api.sambanova.ai/v1"
    DEFAULT_MODEL = "MiniMax-M2.5"
    DEFAULT_TIMEOUT = 120
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY_CODEX")
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout
        self._session = requests.Session()
        
        if not self.api_key:
            logger.warning("No API key provided. Set OPENAI_API_KEY_CODEX environment variable.")
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _build_payload(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 16384)
        }
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 16384
    ) -> str:
        """Send a chat request to the API."""
        if not self.api_key:
            raise ValueError("API key is required. Set OPENAI_API_KEY_CODEX environment variable.")
        
        headers = self._get_headers()
        payload = self._build_payload(messages, temperature=temperature, max_tokens=max_tokens)
        
        try:
            response = self._session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out after {self.timeout}s")
            raise TimeoutError(f"API request timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise RuntimeError(f"API request failed: {e}")
        
        result = response.json()
        try:
            content = result["choices"][0]["message"]["content"]
            finish_reason = result["choices"][0].get("finish_reason", "unknown")
            logger.info(f"API response: finish_reason={finish_reason}, length={len(content) if content else 0}")
            if finish_reason == "length":
                logger.warning("Response was truncated due to max_tokens limit!")
            if not content:
                logger.warning(f"API returned empty content. Full response: {result}")
            return content or ""
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected API response format: {result}")
            raise ValueError(f"Invalid API response format: {e}")
    
    def set_model(self, model: str) -> None:
        """Set the model to use."""
        self.model = model
        logger.info(f"Model set to: {model}")
    
    @property
    def model(self) -> str:
        return self._model
    
    @model.setter
    def model(self, value: str) -> None:
        self._model = value
    
    def close(self) -> None:
        """Close the session."""
        self._session.close()
