from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Base error for anything that goes wrong talking to an LLM."""


class LLMConfigError(LLMError):
    """The provider is not configured (for example, a missing API key)."""


class LLMOutputError(LLMError):
    """The model replied, but the reply failed schema validation."""


class LLMClient(Protocol):
    def complete_text(self, system: str, user: str) -> str: ...
#
    def complete_structured(self, system: str, user: str, schema: type[T]) -> T: ...