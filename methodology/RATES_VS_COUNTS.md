# Rates vs Raw Counts: A Methodological Guide

*In response to Keith and Pam's question about when to use rates vs raw counts*

For every metric in this dataset, we made a deliberate choice about whether to measure it as a **raw count** or as a **rate** (normalized by some denominator). Here's our reasoning for each.

---

## The Core Principle

**Use raw counts when**: You care about absolute impact or total volume
**Use rates when**: You want to compare things of different sizes fairly

The classic example: "Company A introduced 1,000 bugs, Company B introduced 100 bugs." 
- If A has 100x more commits than B, they're actually *better* per-commit
- If they have equal commits, A is genuinely buggier

---

## Metric-by-Metric Analysis

### 1. Bug Lifetime (days/years)

**We use: Raw count (days)**

**Why not a rate?** Lifetime is already inherently comparable across bugs. A bug that survives 1,000 days is worse than one surviving 100 days, regardless of what subsystem it's in or how much code changed.

**When you might want a rate:** If comparing across projects of different ages. A 5-year-old project can't have bugs older than 5 years, so comparing to a 20-year-old project requires normalization by project age.

---

### 2. Bugs per Subsystem

**We use: BOTH, depending on the question**

**Raw count** answers: "Where should we focus fuzzing efforts?" → Subsystems with more total bugs need more attention.

**Rate (bugs per 1K lines, or bugs per commit)** answers: "Which subsystems have the worst code quality?" → A subsystem with 10K bugs but 10M lines is actually cleaner than one with 1K bugs in 100K lines.

**Our default:** We report raw counts in most visualizations because our audience (security researchers) cares about "where are the bugs" not "where is the code cleanest."

---

### 3. Super-Reviewer Identification

**We use: Rate (median bug lifetime for their reviews)**

**Why not raw count of bugs caught?** A reviewer who's been around 20 years will naturally have more reviews than a newcomer. We care about *how quickly* they catch bugs, not *how many* they've reviewed.

**The threshold (50+ fixes) is a raw count** because we need statistical significance. Below 50, the median is too noisy to trust.

---

### 4. Weekend Effect

**We use: Rate (median lifetime by day-of-week)**

**Why rate?** There are fewer weekend commits than weekday commits. If we used raw counts, we'd just see "fewer bugs on weekends" which is obvious and uninteresting.

By using median lifetime *per day*, we ask: "Given that a bug was introduced on Saturday, how long does it survive?" This reveals something non-obvious about review patterns.

---

### 5. Corporate Contributions

**We use: BOTH**

**Raw count** answers: "Who is doing the most kernel security work?" → Important for understanding the ecosystem.

**Rate (% of total)** answers: "What fraction of fixes come from Google vs Red Hat?" → Important for dependency/concentration risk.

**Fix/Introduction ratio** is the most interesting rate: It tells you whether a company is a net positive or negative for kernel stability. A company with ratio > 1 fixes more bugs than they introduce.

---

### 6. Temporal Trends (bugs over time)

**We use: Raw count for bug volume, rate for lifetime trends**

**Why raw counts for volume?** We want to know if the kernel is getting buggier in absolute terms. If 2024 has 2x the bugs of 2014, that matters regardless of codebase growth.

**Why rate for lifetime?** We track *median* lifetime per year, which is already a rate (central tendency of a distribution). This tells us if we're getting faster at finding bugs.

**Alternative we considered:** Bugs per KLOC per year. We rejected this because KLOC growth is hard to measure consistently, and raw bug counts are more actionable for security teams.

---

### 7. Bug Type Analysis (race conditions, UAF, etc.)

**We use: Raw count for prevalence, rate (median lifetime) for severity**

**Raw count** answers: "What kinds of bugs should our fuzzer target?" → If there are 10x more memory bugs than race conditions, prioritize memory bug detection.

**Rate (lifetime)** answers: "Which bug types are hardest to find?" → Race conditions surviving 5x longer than buffer overflows tells us something about detection difficulty.

---

### 8. Author Analysis (who introduces bugs)

**We use: Rate (bugs per commit)**

**Why?** Prolific authors will naturally have more bugs in absolute terms. Linus has the most bugs because he has the most commits. That's not useful.

Bugs-per-commit reveals authors who might benefit from additional review or tooling.

**Caveat:** We don't publish per-author rates publicly because it can be misinterpreted as shaming. We use this internally for understanding patterns.

---

### 9. Review Network Analysis

**We use: Raw counts (edges = number of co-reviews)**

**Why not rate?** For network visualization, edge weight represents collaboration intensity. Two people who've reviewed 100 of the same patches together are more connected than two who've reviewed 10, regardless of their individual review volumes.

---

## Decision Framework

When adding a new metric, ask:

1. **What question am I answering?**
   - "How much total X?" → Raw count
   - "How does X compare across differently-sized groups?" → Rate

2. **What's my denominator if I use a rate?**
   - Per commit? Per line of code? Per time period?
   - The denominator should be something you can measure reliably

3. **What would a naive reader conclude from raw counts?**
   - If it's misleading (e.g., "big subsystems have more bugs"), use a rate
   - If it's actionable (e.g., "this subsystem needs attention"), raw count is fine

4. **Am I comparing across groups of different sizes?**
   - Yes → Probably need a rate
   - No → Raw count is fine

---

## Common Pitfalls

### Pitfall 1: Using rates when raw counts matter

"Subsystem X has the lowest bug rate per KLOC!"

But if X has 100 lines of code and Y has 10 million, Y's bugs matter more for security even if its rate is higher.

### Pitfall 2: Using raw counts when rates matter

"Developer A introduced 500 bugs!"

If A has 50,000 commits and B has 1,000 commits with 50 bugs, B is the one with the problem.

### Pitfall 3: Inconsistent denominators

Comparing "bugs per commit" for one company to "bugs per developer" for another. Always use the same denominator when comparing.

### Pitfall 4: Rates on small samples

"This subsystem has 0.5 bugs per commit!"

...but it only has 2 commits. The rate is meaningless. Always pair rates with sample sizes.

---

## Summary Table

| Metric | We Use | Rationale |
|--------|--------|-----------|
| Bug lifetime | Raw (days) | Already comparable |
| Bugs per subsystem | Both | Count for prioritization, rate for quality |
| Super-reviewer threshold | Raw (50+) | Statistical significance |
| Super-reviewer speed | Rate (median lifetime) | Compare across different volumes |
| Weekend effect | Rate (median by day) | Adjust for fewer weekend commits |
| Corporate contributions | Both | Count for volume, rate for comparison |
| Temporal trends | Both | Count for volume, rate for improvement |
| Bug type prevalence | Raw count | Prioritization |
| Bug type severity | Rate (lifetime) | Difficulty comparison |
| Author bugginess | Rate (per commit) | Fair comparison |
| Review networks | Raw count | Edge weight = intensity |

---

*This document should be updated whenever we add new metrics to ensure we're being intentional about rate vs count decisions.*
