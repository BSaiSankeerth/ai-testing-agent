import secrets
import time
from dataclasses import dataclass, field
#

@dataclass
class RunIdentity:
    """Throwaway account details generated once per test run."""

    email: str
    username: str
    password: str = field(repr=False)
    registered: bool = False  # set True once valid registration passes

    @classmethod
    def new(cls, domain: str = "example.com") -> "RunIdentity":
        tag = f"{int(time.time())}{secrets.token_hex(2)}"
        return cls(
            email=f"qa.{tag}@{domain}",
            username=f"qa_{tag}",
            password="Qa1!" + secrets.token_hex(6),
        )

    def resolve(self, placeholder: str) -> str:
        values = {
            "{{unique_email}}": self.email,
            "{{existing_email}}": self.email,
            "{{unique_username}}": self.username,
            "{{valid_password}}": self.password,
            "{{wrong_password}}": self.password + "x9",
            "{{invalid_email}}": "not-an-email",
            "{{empty}}": "",
        }
        if placeholder not in values:
            raise ValueError(f"Unknown placeholder: {placeholder}")
        return values[placeholder]