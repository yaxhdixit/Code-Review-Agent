"""Unit tests for git diff extraction and credential sanitization."""

import unittest
from unittest.mock import MagicMock, patch

from code_review_agent.cli import create_parser, parse_args
from code_review_agent.git import GitError, get_git_diff, sanitize_diff


class TestGitSanitizer(unittest.TestCase):
    def test_sanitize_private_keys(self):
        raw = (
            "diff --git a/key.pem b/key.pem\n"
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEowIBAAKCAQEA0m...\n"
            "-----END RSA PRIVATE KEY-----\n"
        )
        sanitized = sanitize_diff(raw)
        self.assertNotIn("MIIEowIBAAKCAQEA0m", sanitized)
        self.assertIn("[REDACTED PRIVATE KEY]", sanitized)

    def test_sanitize_bearer_token(self):
        raw = 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz'
        sanitized = sanitize_diff(raw)
        self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", sanitized)
        self.assertIn("Bearer [REDACTED]", sanitized)

    def test_sanitize_api_keys(self):
        raw = 'api_key: "AIzaSyD-12345abcdef67890"\nOPENAI_API_KEY = "sk-proj-123456789abcdef"'
        sanitized = sanitize_diff(raw)
        self.assertNotIn("AIzaSyD-12345abcdef67890", sanitized)
        self.assertNotIn("sk-proj-123456789abcdef", sanitized)
        self.assertIn("[REDACTED]", sanitized)

    def test_empty_diff(self):
        self.assertEqual(sanitize_diff(""), "")
        self.assertEqual(sanitize_diff(None), "")


class TestGitDiff(unittest.TestCase):
    @patch("subprocess.run")
    def test_get_git_diff_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="diff --git a/foo.py b/foo.py\n+print('hello')\n", stderr="")
        res = get_git_diff(staged=True)
        self.assertIn("+print('hello')", res)
        mock_run.assert_called_with(
            ["git", "diff", "--cached"],
            stdout=-1,
            stderr=-1,
            text=True,
            cwd=None,
            check=False,
        )

    @patch("subprocess.run")
    def test_get_git_diff_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=128, stdout="", stderr="fatal: not a git repository")
        with self.assertRaises(GitError):
            get_git_diff()


class TestCliArgs(unittest.TestCase):
    def test_default_args(self):
        args = parse_args([])
        self.assertIsNone(args.diff)
        self.assertFalse(args.staged)
        self.assertEqual(args.provider, "gemini")
        self.assertFalse(args.dry_run)

    def test_custom_flags(self):
        args = parse_args(["--diff", "origin/main", "--provider", "openai", "--dry-run", "--json"])
        self.assertEqual(args.diff, "origin/main")
        self.assertEqual(args.provider, "openai")
        self.assertTrue(args.dry_run)
        self.assertTrue(args.json)


if __name__ == "__main__":
    unittest.main()
