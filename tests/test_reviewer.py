"""Unit tests for ReviewEngine and ReviewResult formatting."""

import json
import unittest
from unittest.mock import MagicMock

from code_review_agent.reviewer import ReviewEngine, ReviewResult


class TestReviewer(unittest.TestCase):
    def test_review_result_markdown(self):
        result = ReviewResult(
            summary="Found critical vulnerability",
            verdict="REQUEST_CHANGES",
            issues=[
                {
                    "file": "server.py",
                    "line": 42,
                    "category": "security",
                    "severity": "critical",
                    "title": "SQL Injection",
                    "description": "User input passed directly to cursor.execute",
                    "suggestion": "Use parameterized query",
                }
            ],
        )
        md = result.to_markdown()
        self.assertIn("# 🤖 Code Review Agent Report", md)
        self.assertIn("❌ Changes Requested", md)
        self.assertIn("[CRITICAL] SQL Injection", md)
        self.assertIn("`server.py:42`", md)
        self.assertIn("Use parameterized query", md)

    def test_review_result_json(self):
        result = ReviewResult(
            summary="Clean code",
            verdict="APPROVE",
            issues=[],
        )
        data = json.loads(result.to_json())
        self.assertEqual(data["verdict"], "APPROVE")
        self.assertEqual(data["issues"], [])

    def test_review_engine_with_mock_provider(self):
        mock_provider = MagicMock()
        mock_provider.complete.return_value = json.dumps({
            "summary": "LGTM",
            "verdict": "APPROVE",
            "issues": [],
        })

        engine = ReviewEngine(provider=mock_provider)
        res = engine.review("diff --git a/a.py b/a.py\n+print(1)")
        self.assertEqual(res.verdict, "APPROVE")
        self.assertEqual(res.summary, "LGTM")
        self.assertEqual(res.issues, [])
        mock_provider.complete.assert_called_once()

    def test_review_engine_truncation(self):
        mock_provider = MagicMock()
        mock_provider.complete.return_value = '{"summary": "ok", "verdict": "APPROVE", "issues": []}'
        engine = ReviewEngine(provider=mock_provider)
        huge_diff = "a" * (ReviewEngine.MAX_DIFF_CHARS + 500)
        engine.review(huge_diff)
        sent_prompt = mock_provider.complete.call_args[0][0]
        self.assertIn("Diff truncated due to size limits", sent_prompt)


if __name__ == "__main__":
    unittest.main()
