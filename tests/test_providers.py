"""Unit tests for multi-provider LLM clients."""

import json
import unittest
from unittest.mock import MagicMock, patch

from code_review_agent.providers import (
    AnthropicProvider,
    GeminiProvider,
    OpenAIProvider,
    ProviderError,
    get_provider,
)


class TestProviders(unittest.TestCase):
    def test_missing_api_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ProviderError):
                GeminiProvider()
            with self.assertRaises(ProviderError):
                OpenAIProvider()
            with self.assertRaises(ProviderError):
                AnthropicProvider()

    def test_get_provider_factory(self):
        gemini = get_provider("gemini", api_key="test-key")
        self.assertIsInstance(gemini, GeminiProvider)
        openai = get_provider("openai", api_key="test-key")
        self.assertIsInstance(openai, OpenAIProvider)
        anthropic = get_provider("anthropic", api_key="test-key")
        self.assertIsInstance(anthropic, AnthropicProvider)

        with self.assertRaises(ValueError):
            get_provider("unsupported-provider")

    @patch("urllib.request.urlopen")
    def test_gemini_complete(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "candidates": [
                {"content": {"parts": [{"text": '{"summary": "Looks good", "verdict": "APPROVE", "issues": []}'}]}}
            ]
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        provider = GeminiProvider(api_key="test-key")
        res = provider.complete("Test prompt")
        self.assertIn('"verdict": "APPROVE"', res)

    @patch("urllib.request.urlopen")
    def test_openai_complete(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": '{"summary": "OpenAI approved", "verdict": "APPROVE", "issues": []}'}}]
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        provider = OpenAIProvider(api_key="test-key")
        res = provider.complete("Test prompt")
        self.assertIn('"summary": "OpenAI approved"', res)

    @patch("urllib.request.urlopen")
    def test_anthropic_complete(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "content": [{"text": '{"summary": "Anthropic review", "verdict": "APPROVE", "issues": []}'}]
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        provider = AnthropicProvider(api_key="test-key")
        res = provider.complete("Test prompt")
        self.assertIn('"summary": "Anthropic review"', res)


if __name__ == "__main__":
    unittest.main()
