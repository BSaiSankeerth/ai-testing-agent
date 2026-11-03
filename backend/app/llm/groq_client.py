import json

from groq import Groq
from pydantic import ValidationError

from app.core.config import get_settings
from app.llm.base import LLMConfigError, LLMError, LLMOutputError, T


class GroqClient:
    def __init__(self, model: str | None = None):
        settings = get_settings()
        if not settings.groq_api_key:
            raise LLMConfigError("GROQ_API_KEY is not set in .env")
        self.model = model or settings.llm_model
        self._client = Groq(api_key=settings.groq_api_key.get_secret_value())

    def _chat(self, messages: list[dict], json_mode: bool = False) -> str:
        kwargs = {"model": self.model, "messages": messages, "temperature": 0.2}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = self._client.chat.completions.create(**kwargs)
        except Exception as exc:  # network, auth, rate limit, bad model name
            raise LLMError(f"Groq request failed: {type(exc).__name__}: {exc}") from exc
        return response.choices[0].message.content or ""

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
                raise LLMOutputError(f"Model output invalid twice: {second_error}") from second_error