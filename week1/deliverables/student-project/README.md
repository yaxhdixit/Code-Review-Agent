# Week 1 AI-Native Project: Uncertainty-Aware Code Review Agent

An empirical and decision-theoretic AI code review agent designed to make high-stakes gating decisions under partial observability and asymmetric error costs.

---

## 1. Project Overview

Modern automated code review tools fail because they treat review as a symmetric classification problem. Missing a severe security vulnerability costs \$25,000+ in production downtime and data breach remediation; interrupting a senior engineer for a routine review costs \$80; running an automated test container costs \$5.

This project implements a **Partially Observable Markov Decision Process (POMDP)** agent that:
1. Tracks a 4-state latent quality distribution: `Clean`, `Cosmetic Flaw`, `Functional Bug`, and `Critical Vulnerability`.
2. Updates beliefs using Bayesian conditioning over noisy signals (git diffs, subsystem risk profiles, author experience, and static analysis).
3. Minimizes expected operational loss by choosing among 4 actions: `Approve`, `Request Targeted Tests`, `Escalate to Senior Dev`, and `Block`.

---

## 2. Directory Structure

```text
week1/deliverables/student-project/
├── README.md                          # Project documentation and reproduction guide
├── research-file.md                   # AI research synthesis, terms, queries, and communities
├── discussion-record.md               # Technical community discussions on Reddit & X
├── review-record.md                   # Multi-agent audits (Practitioner, Probability, Preprint)
├── paper/
│   ├── main.tex                       # Complete IJCAI-style LaTeX source
│   ├── references.bib                 # Bibliography
│   ├── figures/                       # Paper figures and architecture diagrams
│   └── preprint.pdf                   # Compiled publication preprint
├── src/
│   └── agent.py                       # POMDP agent, belief updater, and loss matrix
├── data/
│   ├── generate_dataset.py            # Dataset generator script
│   └── test_cases.json                # 40 labeled benchmark pull request scenarios
├── experiments/
│   └── run_experiment.py              # Comparative policy evaluation harness
├── results/
│   ├── experiment_results.json        # Raw confusion matrices, costs, and Brier scores
│   └── summary.md                     # Markdown evaluation summary & failure analyses
├── decisions/
│   └── probability-decision-record.md # Formal Bayesian probability decision record
└── social/
    ├── linkedin-post.md               # LinkedIn technical announcement post
    └── x-thread.md                    # X (Twitter) technical breakdown thread
```

---

## 3. Reproduction Instructions

### Prerequisites
- Python 3.9+ (Zero external pip dependencies required; uses Python standard library).

### Step 1: Generate the Benchmark Dataset
```bash
python3 week1/deliverables/student-project/data/generate_dataset.py
```
This generates `week1/deliverables/student-project/data/test_cases.json` containing 40 ground-truth labeled pull requests across 7 software subsystems.

### Step 2: Run the Policy Comparison Experiment
```bash
python3 week1/deliverables/student-project/experiments/run_experiment.py
```
This executes the comparative evaluation of:
1. **Policy A (Bayesian Cost Minimization)**
2. **Policy B (Naive LLM Zero-Shot Direct Verdict)**
3. **Baseline (Static Linters & Churn Rules)**

Outputs are written to:
- `week1/deliverables/student-project/results/experiment_results.json`
- `week1/deliverables/student-project/results/summary.md`

### Step 3: Run Unit and Integration Tests
```bash
python3 -m unittest discover -s tests
```

### Step 4: Compile the Preprint Paper
Compile the LaTeX document to PDF using `tectonic` or `pdflatex`:
```bash
cd week1/deliverables/student-project/paper
tectonic main.tex
# or: pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

---

## 4. Key Experimental Results

| Policy | Precision | Recall | False Negatives (Escaped) | Total Decision Cost ($) | Mean Brier Score |
|---|---|---|---|---|---|
| **Bayesian POMDP (Ours)** | 40.0% | **100.0%** | **0** | **\$1,900.00** | **0.1729** |
| Naive LLM Zero-Shot | **57.1%** | 50.0% | 8 | \$87,390.00 | 0.2900 |
| Heuristic Baseline | 40.0% | 25.0% | 12 | \$139,920.00 | 0.3100 |

- **Zero Critical Escapes:** The Bayesian cost-minimization policy eliminated all catastrophic false negatives on security-critical pull requests.
- **97.8% Cost Reduction:** Total operational loss dropped from \$87,390 to \$1,900 by preventing expensive outages while curbing unnecessary senior engineer escalations.

---

## 5. Deliverables Completion Checklist

- [x] **One problem for all work:** Code review agent under incomplete information (Section 3 & 12).
- [x] **AI research file:** `research-file.md` with terms, search queries, 7 Reddit communities, 15 X accounts, 5 papers, research questions, and AI error analysis.
- [x] **Discussion record:** `discussion-record.md` documenting technical interactions across Reddit and X with resulting design changes.
- [x] **Agent design & build:** `src/agent.py` implementing inputs, hidden states, belief updates, actions, loss matrix, and Bayesian policy.
- [x] **Benchmark test cases:** `data/test_cases.json` with 40 labeled PR scenarios.
- [x] **Policy comparison experiment:** `experiments/run_experiment.py` evaluating 3 policies on Confusion Matrix, Precision, Recall, Costs, and Calibration.
- [x] **Failure mode analysis:** 5 named failure conditions analyzed for cost in `results/summary.md`.
- [x] **Probability decision record:** `decisions/probability-decision-record.md` with prior, likelihood, and posterior calculation.
- [x] **AI reviews:** `review-record.md` covering Practitioner, Probability, and Preprint audits with accepted/rejected justifications.
- [x] **IJCAI-style preprint:** `paper/main.tex` and `paper/references.bib` covering all 12 required sections.
- [x] **Social media posts:** `social/linkedin-post.md` and `social/x-thread.md`.
- [x] **Ethical considerations & limitations:** Documented in paper and discussion records.
