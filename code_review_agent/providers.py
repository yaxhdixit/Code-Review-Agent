"""LLM provider dispatchers for Gemini, OpenAI, and Anthropic using standard library."""

import json
import os
import urllib.error
import urllib.request
from typing import Dict, Optional


class ProviderError(RuntimeError):
    """Raised when an LLM provider request fails, times out, or receives an error."""
    pass


class BaseProvider:
    """Abstract base provider interface."""

    def complete(self, prompt: str) -> str:
        raise NotImplementedError


class GeminiProvider(BaseProvider):
    """Google Gemini API dispatcher via generativeLanguage REST API."""

    DEFAULT_MODEL = "gemini-1.5-flash"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ProviderError("GEMINI_API_KEY environment variable is missing or empty")
        self.model = model or self.DEFAULT_MODEL

    def complete(self, prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}]
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            raise ProviderError(f"Gemini API error ({err.code}): {err_body}") from err
        except urllib.error.URLError as err:
            raise ProviderError(f"Gemini connection failed: {err.reason}") from err


class OpenAIProvider(BaseProvider):
    """OpenAI API dispatcher via chat completions REST API."""

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY environment variable is missing or empty")
        self.model = model or self.DEFAULT_MODEL

    def complete(self, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert senior code reviewer."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            raise ProviderError(f"OpenAI API error ({err.code}): {err_body}") from err
        except urllib.error.URLError as err:
            raise ProviderError(f"OpenAI connection failed: {err.reason}") from err


class AnthropicProvider(BaseProvider):
    """Anthropic API dispatcher via messages REST API."""

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ProviderError("ANTHROPIC_API_KEY environment variable is missing or empty")
        self.model = model or self.DEFAULT_MODEL

    def complete(self, prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        payload = json.dumps({
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["content"][0]["text"]
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            raise ProviderError(f"Anthropic API error ({err.code}): {err_body}") from err
        except urllib.error.URLError as err:
            raise ProviderError(f"Anthropic connection failed: {err.reason}") from err


PROVIDERS: Dict[str, type] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def get_provider(
    name: str = "gemini",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> BaseProvider:
    """Instantiate and return the configured provider."""
    provider_cls = PROVIDERS.get(name.lower())
    if not provider_cls:
        raise ValueError(
            f"Unsupported provider: '{name}'. Supported: {', '.join(PROVIDERS.keys())}"
        )
    return provider_cls(api_key=api_key, model=model)
