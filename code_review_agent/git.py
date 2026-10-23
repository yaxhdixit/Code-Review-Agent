"""Git interaction and diff sanitization utilities."""

import re
import subprocess
from typing import Optional


class GitError(RuntimeError):
    """Raised when git command fails or current directory is not a git repository."""
    pass


def get_git_diff(
    target: Optional[str] = None,
    staged: bool = False,
    cwd: Optional[str] = None,
) -> str:
    """Extract git diff from current repository.
    
    Args:
        target: Optional branch or commit reference to compare against (e.g. origin/main).
        staged: If True, extract staged changes (--cached).
        cwd: Optional working directory.
    
    Returns:
        The extracted diff text as string.
    """
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--cached")
    elif target:
        cmd.append(target)

    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            check=False,
        )
    except FileNotFoundError as err:
        raise GitError("git executable not found in PATH") from err

    if res.returncode != 0:
        raise GitError(f"git diff failed (exit code {res.returncode}): {res.stderr.strip()}")

    diff = res.stdout
    # If no target and no staged flag specified, and working-tree diff is empty, try cached diff
    if not diff.strip() and not staged and not target:
        cached_res = subprocess.run(
            ["git", "diff", "--cached"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            check=False,
        )
        if cached_res.returncode == 0 and cached_res.stdout.strip():
            diff = cached_res.stdout

    return diff


def sanitize_diff(diff_text: str) -> str:
    """Redact private keys, bearer tokens, and secrets from diff text."""
    if not diff_text:
        return ""

    # Redact PEM private keys
    sanitized = re.sub(
        r"-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----",
        "[REDACTED PRIVATE KEY]",
        diff_text,
    )

    # Redact Bearer tokens
    sanitized = re.sub(
        r"\b(Bearer)\s+[A-Za-z0-9._~+/=-]+",
        r"\1 [REDACTED]",
        sanitized,
        flags=re.IGNORECASE,
    )

    # Redact common API key/token patterns
    sanitized = re.sub(
        r"""(?i)(["']?\b[a-zA-Z0-9_]*(?:api[_-]?key|secret|token|password|auth(?:orization)?)[a-zA-Z0-9_]*["']?\s*[:=]\s*["']?)([a-zA-Z0-9_\-.~+/=]{8,})(["']?)""",
        r'\1[REDACTED]\3',
        sanitized,
    )

    return sanitized
