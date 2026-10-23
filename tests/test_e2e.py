"""End-to-end tests for CLI execution and full review flow."""

import io
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from code_review_agent.cli import main


class TestEndToEnd(unittest.TestCase):
    @patch("code_review_agent.cli.get_git_diff")
    def test_e2e_dry_run(self, mock_diff):
        mock_diff.return_value = "diff --git a/app.py b/app.py\n+password = 'supersecret123'\n"
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["--dry-run"])

        self.assertEqual(exit_code, 0)
        output = stdout_buf.getvalue()
        self.assertIn("--- Extracted & Sanitized Diff (Dry Run) ---", output)
        self.assertIn("[REDACTED]", output)
        self.assertNotIn("supersecret123", output)

    @patch("code_review_agent.cli.get_git_diff")
    def test_e2e_empty_diff(self, mock_diff):
        mock_diff.return_value = ""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        self.assertIn("No changes found to review.", stdout_buf.getvalue())

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    @patch("code_review_agent.reviewer.ReviewEngine.review")
    @patch("code_review_agent.cli.get_git_diff")
    def test_e2e_full_review_markdown_and_file_output(self, mock_diff, mock_review):
        from code_review_agent.reviewer import ReviewResult

        mock_diff.return_value = "diff --git a/foo.py b/foo.py\n+import os\n"
        mock_review.return_value = ReviewResult(
            summary="All good",
            verdict="APPROVE",
            issues=[],
        )

        with tempfile.NamedTemporaryFile("w+", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            stdout_buf = io.StringIO()
            with patch("sys.stdout", stdout_buf):
                exit_code = main(["--diff", "origin/main", "--output", tmp_path])

            self.assertEqual(exit_code, 0)
            self.assertIn("Code Review Agent Report", stdout_buf.getvalue())
            self.assertIn("Approved", stdout_buf.getvalue())

            with open(tmp_path, "r", encoding="utf-8") as f:
                saved = f.read()
            self.assertIn("Code Review Agent Report", saved)
            self.assertIn("Approved", saved)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    @patch("code_review_agent.reviewer.ReviewEngine.review")
    @patch("code_review_agent.cli.get_git_diff")
    def test_e2e_json_output(self, mock_diff, mock_review):
        from code_review_agent.reviewer import ReviewResult

        mock_diff.return_value = "diff --git a/foo.py b/foo.py\n+import os\n"
        mock_review.return_value = ReviewResult(
            summary="Found styling issue",
            verdict="COMMENT",
            issues=[
                {
                    "file": "foo.py",
                    "line": 1,
                    "category": "style",
                    "severity": "suggestion",
                    "title": "Unused import",
                    "description": "os is imported but never used",
                    "suggestion": "Remove import os",
                }
            ],
        )

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["--json"])

        self.assertEqual(exit_code, 0)
        parsed = json.loads(stdout_buf.getvalue())
        self.assertEqual(parsed["verdict"], "COMMENT")
        self.assertEqual(len(parsed["issues"]), 1)
        self.assertEqual(parsed["issues"][0]["category"], "style")


if __name__ == "__main__":
    unittest.main()
