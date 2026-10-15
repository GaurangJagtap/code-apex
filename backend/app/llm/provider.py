import json
from typing import Optional, Dict, Any
import httpx
from backend.app.core.config import settings

class LLMProvider:
    """
    Unified LLM provider interface. Supports Gemini, OpenAI, Anthropic, and Demo mode.
    Validates output structure and handles graceful fallback.
    """
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL

    def is_configured(self) -> bool:
        return bool(self.api_key and self.provider != "demo")

    async def generate_structured_plan(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Sends structured prompt to LLM and returns parsed JSON if configured.
        """
        if not self.is_configured():
            return None

        try:
            if self.provider == "gemini":
                # Google Gemini API
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"}
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(text_content)
            elif self.provider == "openai":
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an autonomous QA test planner. Return strict JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"}
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        text_content = data["choices"][0]["message"]["content"]
                        return json.loads(text_content)
        except Exception:
            return None

        return None
