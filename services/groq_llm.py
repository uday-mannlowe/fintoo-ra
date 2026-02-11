import json
import logging
from typing import Any, Dict, Optional

import requests

from config import settings

logger = logging.getLogger(__name__)


class GroqRetirementAdvisor:
    """
    Groq LLM client that returns retirement assumptions for the engine.
    Falls back to None if API is not configured or response is invalid.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.timeout_s = settings.GROQ_TIMEOUT_S
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def get_assumptions(self, user_snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            logger.info("GROQ_API_KEY not set; using default engine assumptions.")
            return None

        payload = self._build_payload(user_snapshot)

        try:
            response = requests.post(
                self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_s,
            )
            if response.status_code >= 400:
                logger.warning(f"Groq error {response.status_code}: {response.text}")
                return None
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._safe_json_parse(content)
        except Exception as e:
            logger.warning(f"Groq LLM failed; using defaults. Error: {e}")
            return None

    def _build_payload(self, user_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        system_msg = (
            "You are a cautious retirement CFO assistant. "
            "Return only strict JSON matching the schema. "
            "No prose, no markdown."
        )

        schema = {
            "general_inflation": "number (0.02 - 0.10)",
            "healthcare_inflation": "number (0.04 - 0.12)",
            "pre_retirement_return": "number (0.05 - 0.18)",
            "post_retirement_return": "number (0.03 - 0.10)",
            "life_expectancy": "integer (75 - 100)",
            "safety_buffer_years": "integer (0 - 10)",
            "rationale": "short string",
        }

        user_msg = {
            "task": "Analyze the user snapshot and suggest realistic planning assumptions.",
            "constraints": "Be conservative. Favor stability over optimism.",
            "schema": schema,
            "user_snapshot": user_snapshot,
        }

        return {
            "model": self.model,
            "temperature": 0.2,
            "max_tokens": 400,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": json.dumps(user_msg, default=str)},
            ],
        }

    def _safe_json_parse(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(text)
        except Exception:
            # Try to extract the first JSON object from the response
            try:
                start = text.find("{")
                end = text.rfind("}")
                if start >= 0 and end > start:
                    return json.loads(text[start : end + 1])
            except Exception:
                pass
        return None
