# X (Twitter) Thread: Uncertainty-Aware Code Review Agent

*(Attach `preprint.pdf` or paper screenshot to Tweet 1)*

---

### Tweet 1 (The Hook & Problem)
Most AI code review bots get disabled within a week because they spam devs with low-confidence nits or miss subtle 3 AM production crashes.

We redesigned PR review as a decision-theoretic POMDP under partial observability.

Preprint + open-source code below 🧵👇 (1/6)

---

### Tweet 2 (The Hidden State & Cost Asymmetry)
Why? Code review is governed by radical cost asymmetry:
- Missing an auth bypass / race condition = $25,000 outage
- Paging a senior engineer for 15 min = $80
- Running an automated test container = $5

Symmetric accuracy is dead. Expected loss minimization is the only rule that survives. (2/6)

---

### Tweet 3 (The Agent Design)
Our agent maintains a Bayesian belief over 4 latent states:
1. Clean
2. Cosmetic Flaw
3. Functional Bug
4. Critical Vulnerability

Instead of binary approve/reject, it has 4 actions:
[Approve | Request Targeted Tests | Escalate to Senior Dev | Block] (3/6)

---

### Tweet 4 (The Empirical Test & Results)
We evaluated on 40 benchmark PRs against standard CI linters and a zero-shot LLM baseline:
- Naive LLM Loss: $87,390 (missed 8 silent bugs)
- Heuristic Baseline: $139,920
- Bayesian POMDP Loss: $1,900 (0 critical escapes, 0% missed CVEs) (4/6)

---

### Tweet 5 (What Community Feedback Changed)
Reddit & X discussions with @miltos1 and @asolarlez made us rethink the action space.

Engineers told us: "If you page me on trivial PRs, I will block the bot."

So we added automated targeted test generation before human escalation—cutting human interruptions by 50%. (5/6)

---

### Tweet 6 (Open Question & Code)
Biggest limitation: Observation calibration under flaky CI test suites.

Question for devs & SREs: What defect escape cost vs dev interruption ratio does your team use in practice?

Paper & code: https://github.com/yaxhdixit/Code-Review-Agent/tree/main/week1/deliverables/student-project (6/6)
