"""CLI entry point and command-line argument parsing."""

import argparse
import sys
from typing import List, Optional

from .git import GitError, get_git_diff, sanitize_diff


def create_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="code-review-agent",
        description="Automated AI Code Review Agent for local repos and CI pipelines.",
    )
    parser.add_argument(
        "--diff",
        nargs="?",
        const="HEAD",
        default=None,
        metavar="TARGET",
        help="Git target branch/commit to diff against (e.g. origin/main, HEAD~1).",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Review only staged git changes (--cached).",
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "openai", "anthropic"],
        default="gemini",
        help="LLM provider backend (default: gemini).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model identifier override (e.g. gemini-1.5-pro, gpt-4o, claude-3-5-sonnet).",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write review output to specified file path instead of stdout only.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output review as JSON format.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract and sanitize diff without invoking LLM provider API.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    return parser


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse and validate command line arguments."""
    parser = create_parser()
    return parser.parse_args(args)


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI execution routine.
    
    Returns:
        0 on success / clean execution.
        1 on runtime error, git failure, or configuration error.
    """
    try:
        args = parse_args(argv)
    except SystemExit as err:
        return int(err.code) if err.code is not None else 0

    try:
        diff_text = get_git_diff(target=args.diff, staged=args.staged)
    except GitError as err:
        sys.stderr.write(f"Error: {err}\n")
        return 1

    sanitized = sanitize_diff(diff_text)
    if not sanitized.strip():
        sys.stdout.write("No changes found to review.\n")
        return 0

    if args.dry_run:
        sys.stdout.write("--- Extracted & Sanitized Diff (Dry Run) ---\n")
        sys.stdout.write(sanitized)
        if not sanitized.endswith("\n"):
            sys.stdout.write("\n")
        return 0

    # In task T-1, LLM reviewer integration is hooked via providers in T-2.
    try:
        from .reviewer import ReviewEngine
        engine = ReviewEngine(provider_name=args.provider, model=args.model)
        result = engine.review(sanitized)
        output_text = result.to_json() if args.json else result.to_markdown()
    except ImportError:
        output_text = f"Review engine placeholder for provider '{args.provider}'. Diff size: {len(sanitized)} bytes."

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_text)
                if not output_text.endswith("\n"):
                    f.write("\n")
        except OSError as err:
            sys.stderr.write(f"Error writing to output file '{args.output}': {err}\n")
            return 1

    sys.stdout.write(output_text)
    if not output_text.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
