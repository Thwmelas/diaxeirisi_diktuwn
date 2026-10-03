"""
LLM client.
Responsible: Member 3

Talks to a local model served by Ollama (https://ollama.com). Uses only the
Python standard library, so no extra dependency is needed.

Setup:
    1. Install Ollama, then:  ollama pull llama3.2:3b
    2. Ollama listens on http://localhost:11434 by default.

Configuration via environment variables:
    OLLAMA_URL      (default http://localhost:11434)
    OLLAMA_MODEL    (default llama3.2:3b)
    OLLAMA_TIMEOUT  seconds (default 30)
"""

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class LLMUnavailable(RuntimeError):
    """Raised when the model server cannot be reached or errors out."""


class OllamaClient:
    def __init__(
        self,
        model: Optional[str] = None,
        url: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: float = 0.0,
        json_schema: Optional[Dict[str, Any]] = None,
    ):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.url = (url or os.getenv("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self.timeout = float(timeout or os.getenv("OLLAMA_TIMEOUT", "30"))
        self.temperature = temperature
        self.json_schema = json_schema

    @property
    def name(self) -> str:
        return f"ollama:{self.model}"

    def complete(self, system: str, user: str) -> str:
        """Send one chat request and return the model's text reply."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            # Structured output: Ollama constrains generation to this schema.
            "format": self.json_schema or "json",
            "options": {"temperature": self.temperature},
        }
        request = urllib.request.Request(
            f"{self.url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:200]
            raise LLMUnavailable(f"Ollama HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise LLMUnavailable(f"Cannot reach Ollama at {self.url}: {exc}") from exc

        try:
            return body["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMUnavailable(f"Unexpected Ollama response: {str(body)[:200]}") from exc

    def is_available(self) -> bool:
        """Quick health check: is the server up and is the model pulled?"""
        try:
            with urllib.request.urlopen(f"{self.url}/api/tags", timeout=3) as response:
                tags = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return False
        names = {m.get("name", "") for m in tags.get("models", [])}
        return any(n == self.model or n.split(":")[0] == self.model for n in names)
