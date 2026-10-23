# Product specification — Code-Review-Agent

> Status: draft. A coding agent must not implement product code until this specification is approved through Genesis.

## Problem

Software developers and CI/CD pipelines need automated, fast, context-aware code reviews on pull requests and local changes before merging, identifying bugs, security vulnerabilities, performance regressions, and style issues without requiring manual inspection for every incremental commit.

## Users

1. Software Engineers reviewing their staged/unstaged changes locally before committing.
2. Code Reviewers and Maintainers using automated PR reviews to accelerate code reviews.
3. CI/CD Systems (e.g. GitHub Actions) running automated quality gates on PRs.

## Functional requirements

- FR-1: Parse git changes from local working directory (staged, unstaged, or branch diff against a target base such as origin/main).
- FR-2: Support multi-provider LLM backends (Google Gemini, OpenAI, Anthropic) selectable via CLI argument or environment variable, using corresponding API keys (GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY).
- FR-3: Perform automated review evaluating code correctness, logic bugs, security vulnerabilities (e.g., OWASP issues, leaked credentials), and performance bottlenecks.
- FR-4: Output review results in human-readable Markdown format in terminal, and optionally write to a file or JSON output for CI pipeline consumption.
- FR-5: Provide GitHub Actions CI workflow integration capability to post review comments or summaries on pull requests.

## Non-functional requirements

- NFR-1: Zero external dependencies in core runtime — implement using Python 3 standard library (argparse, subprocess, urllib.request, json).
- NFR-2: Fail gracefully with clear actionable error messages when API keys are missing, network requests timeout, or git diffs are empty.
- NFR-3: Review execution latency bounded strictly by provider API response time; local diff extraction and prompt assembly completes in under 1 second.
- NFR-4: Respect privacy and security by strictly scoping analyzed diffs to repository code and redacting recognized credential strings before sending to LLMs if configured.

## Constraints

- Runtime must require only Python 3.9+ with standard library modules.
- LLM API calls require active internet connectivity and valid provider API keys.
- Token limits of LLM providers must be handled by chunking or truncating diffs that exceed provider context windows.

## Non-goals

- Automatic code modification or auto-commit / auto-merge functionality (review agent is advisory only).
- Running interactive multi-agent chat sessions during CI execution.
- Self-hosted model weight training or fine-tuning infrastructure.

## Acceptance criteria

- AC-1: Running `python3 -m code_review_agent --diff` on a repository with staged/unstaged changes extracts git diff and prints a structured markdown review.
- AC-2: Support `--provider [gemini|openai|anthropic]` with correct API payload formatting and response parsing for each supported provider.
- AC-3: Automated self-tests pass verifying diff parser, prompt generation, error handling on invalid keys/empty diffs, and mock provider interactions.
- AC-4: CLI returns exit code 0 on clean/advisory review, and exit code 1 on command failure / configuration error.

## Risks

- Rate limiting or token limit exhaustion by LLM providers on massive diffs. Mitigation: diff truncation warning and per-file batching.
- Cost and privacy implications of external API calls. Mitigation: dry-run mode (`--dry-run`) allowing inspection of diff payload without sending requests.

## Open questions

- None.
