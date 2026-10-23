# Code-Review-Agent

An automated AI-powered Code Review Agent built with zero external runtime dependencies. Runs locally as a CLI tool or inside CI/CD pipelines (e.g. GitHub Actions) to review git diffs for correctness, security vulnerabilities, performance bottlenecks, and style.

## Features

- **Multi-Provider Support**: Pluggable backends for Google Gemini (default), OpenAI, and Anthropic.
- **Zero External Dependencies**: Implemented purely with Python 3.9+ standard library (`urllib.request`, `json`, `argparse`, `subprocess`).
- **Privacy & Security First**: Automatically scrubs API keys, private keys, and bearer tokens from diffs before sending to LLMs.
- **Dry-run Mode**: Inspect sanitized diffs without making external network calls.
- **Flexible Outputs**: Terminal Markdown format and machine-readable JSON.
- **CI/CD Integration**: Ready-to-use GitHub Actions workflow.

## Quick Start

### 1. Environment Setup

Set your API key for your preferred provider:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
# or
export OPENAI_API_KEY="your-openai-api-key"
# or
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 2. Run Locally

Review uncommitted changes in current working directory:
```bash
python3 -m code_review_agent
```

Review staged changes only:
```bash
python3 -m code_review_agent --staged
```

Review diff against a base branch:
```bash
python3 -m code_review_agent --diff origin/main
```

Use a different provider or custom model:
```bash
python3 -m code_review_agent --provider openai --model gpt-4o
python3 -m code_review_agent --provider anthropic --model claude-3-5-sonnet-20241022
```

Inspect sanitized diff without invoking LLM (Dry Run):
```bash
python3 -m code_review_agent --dry-run
```

Output as JSON:
```bash
python3 -m code_review_agent --json
```

Save report to file:
```bash
python3 -m code_review_agent --output review.md
```

## Running Tests

Run the full unit and end-to-end test suite:
```bash
python3 -m unittest discover -s tests
```

## CI/CD Pipeline

A GitHub Actions workflow is provided at `.github/workflows/code-review.yml` which automatically reviews incoming Pull Requests and posts findings into GitHub Actions summary and PR comments.
