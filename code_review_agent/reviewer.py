"""Code review engine, prompt builder, and structured result formatting."""

import json
import re
from typing import Any, Dict, List, Optional

from .providers import BaseProvider, ProviderError, get_provider

REVIEW_PROMPT_TEMPLATE = """You are an automated senior code review agent.
Review the following git diff carefully.

Review Focus:
1. Correctness & Bugs: Logic flaws, off-by-one errors, uncaught exceptions, race conditions.
2. Security: Vulnerabilities, injection, improper input validation, secret leaks.
3. Performance: Inefficient algorithms, memory leaks, unclosed resources, unnecessary queries.
4. Maintainability: Dead code, missing error handling, complex spaghetti logic.

Format your response as valid JSON with this exact schema:
{
  "summary": "Brief overall summary of changes and review verdict",
  "verdict": "APPROVE" | "REQUEST_CHANGES" | "COMMENT",
  "issues": [
    {
      "file": "path/to/file",
      "line": 42,
      "category": "bug" | "security" | "performance" | "style",
      "severity": "critical" | "warning" | "suggestion",
      "title": "Short title describing issue",
      "description": "Clear explanation of the problem",
      "suggestion": "Concrete fix or code recommendation"
    }
  ]
}

If no issues are found, return "issues": [] and verdict "APPROVE".
Output ONLY the raw JSON block without markdown code fences.

GIT DIFF:
```diff
{diff_text}
```
"""


class ReviewResult:
    """Encapsulates parsed review results."""

    def __init__(
        self,
        summary: str,
        verdict: str,
        issues: List[Dict[str, Any]],
        raw_text: str = "",
    ):
        self.summary = summary
        self.verdict = verdict
        self.issues = issues
        self.raw_text = raw_text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "verdict": self.verdict,
            "issues": self.issues,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        verdict_badge = {
            "APPROVE": "✅ Approved",
            "REQUEST_CHANGES": "❌ Changes Requested",
            "COMMENT": "💬 Comments",
            "ERROR": "⚠️ Provider Error",
        }.get(self.verdict.upper(), self.verdict)

        lines = [
            "# 🤖 Code Review Agent Report",
            "",
            f"**Verdict:** {verdict_badge}",
            "",
            f"**Summary:** {self.summary}",
            "",
        ]

        if not self.issues:
            lines.append("✨ *No issues identified. Code looks clean!*")
            return "\n".join(lines)

        lines.extend([
            "## Identified Issues",
            "",
            f"Found {len(self.issues)} issue(s):",
            "",
        ])

        for idx, item in enumerate(self.issues, 1):
            file_loc = item.get("file", "unknown")
            line_no = item.get("line")
            loc_str = f"`{file_loc}:{line_no}`" if line_no else f"`{file_loc}`"
            sev = item.get("severity", "suggestion").upper()
            cat = item.get("category", "general")
            title = item.get("title", "Review Finding")
            desc = item.get("description", "")
            sugg = item.get("suggestion", "")

            lines.append(f"### {idx}. [{sev}] {title}")
            lines.append(f"- **Location:** {loc_str}")
            lines.append(f"- **Category:** {cat}")
            lines.append(f"- **Details:** {desc}")
            if sugg:
                lines.append(f"- **Suggestion:** {sugg}")
            lines.append("")

        return "\n".join(lines).strip()


class ReviewEngine:
    """Orchestrates diff prompt generation, provider query, and response parsing."""

    MAX_DIFF_CHARS = 120_000

    def __init__(
        self,
        provider_name: str = "gemini",
        model: Optional[str] = None,
        provider: Optional[BaseProvider] = None,
    ):
        self.provider = provider or get_provider(provider_name, model=model)

    def build_prompt(self, diff_text: str) -> str:
        if len(diff_text) > self.MAX_DIFF_CHARS:
            truncated_diff = diff_text[: self.MAX_DIFF_CHARS] + "\n\n... [Diff truncated due to size limits]"
        else:
            truncated_diff = diff_text
        return REVIEW_PROMPT_TEMPLATE.replace("{diff_text}", truncated_diff)

    def review(self, diff_text: str) -> ReviewResult:
        if not diff_text or not diff_text.strip():
            return ReviewResult(
                summary="No changes provided for review.",
                verdict="APPROVE",
                issues=[],
                raw_text="",
            )

        prompt = self.build_prompt(diff_text)
        try:
            raw_response = self.provider.complete(prompt)
            return self._parse_response(raw_response)
        except ProviderError as err:
            return ReviewResult(
                summary=f"Review failed due to provider error: {err}",
                verdict="ERROR",
                issues=[],
                raw_text=str(err),
            )

    def _parse_response(self, raw: str) -> ReviewResult:
        text = raw.strip()
        # Strip potential markdown fences if returned
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

        try:
            data = json.loads(text)
            return ReviewResult(
                summary=data.get("summary", "Review complete."),
                verdict=data.get("verdict", "COMMENT"),
                issues=data.get("issues", []),
                raw_text=raw,
            )
        except json.JSONDecodeError:
            # Fallback if provider didn't return valid JSON
            return ReviewResult(
                summary="Automated review comments returned in unstructured format.",
                verdict="COMMENT",
                issues=[],
                raw_text=raw,
            )
