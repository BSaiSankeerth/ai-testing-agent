import json

from groq import BadRequestError, Groq
from pydantic import ValidationError

from app.core.config import get_settings
from app.llm.base import LLMConfigError, LLMError, LLMOutputError, T

import time
from groq import BadRequestError, Groq, RateLimitError

class GroqClient:
    def __init__(self, model: str | None = None):
        settings = get_settings()
        if not settings.groq_api_key:
            raise LLMConfigError("GROQ_API_KEY is not set in .env")
        self.model = model or settings.llm_model
        self._client = Groq(api_key=settings.groq_api_key.get_secret_value())

    def _chat(self, messages: list[dict], json_mode: bool = False, attempts: int = 3) -> str:
        kwargs = {"model": self.model, "messages": messages, "temperature": 0.2}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
#
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = self._client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ""
            except RateLimitError as exc:
                last_error = exc
                if "per day" in str(exc).lower():
                    raise LLMError("Groq daily quota exhausted; try later or switch model") from exc
                wait = 15 * (attempt + 1)
                print(f"[llm] rate limited, waiting {wait}s (attempt {attempt + 1}/{attempts})", flush=True)
                time.sleep(wait)
                continue
            except BadRequestError as exc:
                # Groq rejected the model's JSON as malformed: just try again.
                if json_mode and "json_validate_failed" in str(exc):
                    last_error = exc
                    continue
                raise LLMError(f"Groq request failed: {str(exc)[:300]}") from exc
            except Exception as exc:  # network, auth, rate limit, bad model name
                raise LLMError(
                    f"Groq request failed: {type(exc).__name__}: {str(exc)[:300]}"
                ) from exc
        raise LLMError(
            f"Groq could not produce valid JSON after {attempts} attempts"
        ) from last_error

    def complete_text(self, system: str, user: str) -> str:
        return self._chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}]
        )

    def complete_structured(self, system: str, user: str, schema: type[T]) -> T:
        schema_json = json.dumps(schema.model_json_schema())
        full_system = (
            f"{system}\n\nReply with a single JSON object that matches this "
            f"JSON schema exactly. No extra text.\n{schema_json}"
        )
        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": user},
        ]
        raw = self._chat(messages, json_mode=True)
        try:
            return schema.model_validate_json(raw)
        except ValidationError as first_error:
            messages += [
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": f"That failed validation:\n{first_error}\nReturn corrected JSON only.",
                },
            ]
            raw = self._chat(messages, json_mode=True)
            try:
                return schema.model_validate_json(raw)
            except ValidationError as second_error:
                raise LLMOutputError(
                    f"Model output invalid twice: {str(second_error)[:300]}"
                ) from second_error