"""Uncertainty-Aware Code Review Agent implementing POMDP belief updates and cost minimization."""

import math
from typing import Dict, List, Tuple

# States: s0: Clean, s1: Cosmetic, s2: Functional Bug, s3: Critical Vulnerability
STATES = ["clean", "cosmetic", "functional_bug", "critical_vulnerability"]

# Actions: a0: Approve, a1: Request Tests, a2: Escalate to Senior Human, a3: Block
ACTIONS = ["approve", "request_tests", "escalate_human", "block"]

# Asymmetric Loss Matrix L(s, a) in USD
LOSS_MATRIX = {
    "clean": {
        "approve": 0,
        "request_tests": 5,
        "escalate_human": 80,
        "block": 300,
    },
    "cosmetic": {
        "approve": 10,
        "request_tests": 15,
        "escalate_human": 80,
        "block": 200,
    },
    "functional_bug": {
        "approve": 2000,
        "request_tests": 50,
        "escalate_human": 120,
        "block": 150,
    },
    "critical_vulnerability": {
        "approve": 25000,
        "request_tests": 200,
        "escalate_human": 200,
        "block": 100,
    },
}

# Subsystem baseline defect priors
SUBSYSTEM_PRIORS = {
    "docs": {"clean": 0.90, "cosmetic": 0.08, "functional_bug": 0.015, "critical_vulnerability": 0.005},
    "frontend_ui": {"clean": 0.65, "cosmetic": 0.20, "functional_bug": 0.12, "critical_vulnerability": 0.03},
    "core_engine": {"clean": 0.50, "cosmetic": 0.15, "functional_bug": 0.25, "critical_vulnerability": 0.10},
    "config": {"clean": 0.70, "cosmetic": 0.15, "functional_bug": 0.10, "critical_vulnerability": 0.05},
    "payments": {"clean": 0.35, "cosmetic": 0.10, "functional_bug": 0.30, "critical_vulnerability": 0.25},
    "auth": {"clean": 0.30, "cosmetic": 0.10, "functional_bug": 0.25, "critical_vulnerability": 0.35},
    "database_migration": {"clean": 0.40, "cosmetic": 0.10, "functional_bug": 0.30, "critical_vulnerability": 0.20},
}


class BayesianCodeReviewAgent:
    """Agent that maintains a belief distribution over latent defect states and acts via decision theory."""

    def __init__(self, loss_matrix: Dict[str, Dict[str, float]] = None):
        self.loss_matrix = loss_matrix or LOSS_MATRIX

    def compute_prior(self, case: Dict) -> Dict[str, float]:
        subsystem = case.get("subsystem", "core_engine")
        base_prior = SUBSYSTEM_PRIORS.get(subsystem, SUBSYSTEM_PRIORS["core_engine"]).copy()

        # Author experience modifier
        experience = case.get("author_experience", "mid")
        if experience == "senior":
            base_prior["clean"] += 0.10
            base_prior["functional_bug"] = max(0.01, base_prior["functional_bug"] - 0.05)
            base_prior["critical_vulnerability"] = max(0.005, base_prior["critical_vulnerability"] - 0.05)
        elif experience == "junior":
            base_prior["clean"] = max(0.10, base_prior["clean"] - 0.15)
            base_prior["functional_bug"] += 0.08
            base_prior["critical_vulnerability"] += 0.07

        # Normalize prior to sum to 1.0
        total = sum(base_prior.values())
        return {s: base_prior[s] / total for s in STATES}

    def compute_likelihood(self, case: Dict) -> Dict[str, float]:
        """Compute P(Evidence | State) based on static signals and diff contents."""
        signals = case.get("static_signals", {})
        linter_clean = signals.get("linter_clean", True)
        unit_tests_pass = signals.get("unit_tests_pass", True)
        sast_flags = signals.get("sast_flags", 0)
        diff_text = case.get("diff", "").lower()

        # Base observation model
        likelihood = {
            "clean": 0.70,
            "cosmetic": 0.70,
            "functional_bug": 0.60,
            "critical_vulnerability": 0.50,
        }

        # Linter feedback
        if not linter_clean:
            likelihood["clean"] *= 0.15
            likelihood["cosmetic"] *= 0.85
            likelihood["functional_bug"] *= 0.60
            likelihood["critical_vulnerability"] *= 0.50

        # SAST security alert
        if sast_flags > 0:
            likelihood["clean"] *= 0.05
            likelihood["cosmetic"] *= 0.10
            likelihood["functional_bug"] *= 0.40
            likelihood["critical_vulnerability"] *= 0.95

        # Heuristic keyword alerts in diff
        high_risk_patterns = ["sql", "execute(", "dangerously", "yaml.load", "jwt_secret", "compare_digest", "password", "flock", "flock"]
        if any(p in diff_text for p in high_risk_patterns):
            likelihood["critical_vulnerability"] *= 1.8
            likelihood["functional_bug"] *= 1.3
            likelihood["clean"] *= 0.4

        return likelihood

    def update_beliefs(self, case: Dict) -> Dict[str, float]:
        """Bayesian belief update: Posterior = (Prior * Likelihood) / Marginal."""
        prior = self.compute_prior(case)
        likelihood = self.compute_likelihood(case)

        unnormalized = {s: prior[s] * likelihood[s] for s in STATES}
        marginal = sum(unnormalized.values())
        if marginal == 0:
            return prior
        return {s: unnormalized[s] / marginal for s in STATES}

    def policy_bayesian_cost_minimization(self, beliefs: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
        """Select action that minimizes expected loss under posterior beliefs."""
        expected_losses = {}
        for a in ACTIONS:
            loss = sum(beliefs[s] * self.loss_matrix[s][a] for s in STATES)
            expected_losses[a] = round(loss, 2)

        best_action = min(expected_losses, key=expected_losses.get)
        return best_action, expected_losses

    def policy_naive_llm_zero_shot(self, case: Dict, beliefs: Dict[str, float]) -> str:
        """Simulates standard LLM zero-shot prompt recommendation (mode-seeking, cost-unaware)."""
        # A standard LLM outputs whichever single state has highest perceived probability,
        # and chooses actions symmetrically without accounting for loss asymmetry.
        predicted_state = max(beliefs, key=beliefs.get)
        if predicted_state == "clean":
            return "approve"
        elif predicted_state == "cosmetic":
            return "approve"  # LLMs routinely approve minor styling nits
        elif predicted_state == "functional_bug":
            return "block"
        else:  # critical
            return "block"

    def policy_heuristic_baseline(self, case: Dict) -> str:
        """Rule-based heuristic baseline (CI static checks)."""
        signals = case.get("static_signals", {})
        if signals.get("sast_flags", 0) > 0:
            return "block"
        if not signals.get("linter_clean", True):
            return "escalate_human"
        diff_stats = case.get("diff_stats", {})
        if diff_stats.get("additions", 0) + diff_stats.get("deletions", 0) > 60:
            return "escalate_human"
        return "approve"
