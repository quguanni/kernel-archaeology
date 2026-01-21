# Limitations

This document provides an honest assessment of what this analysis does and doesn't capture. Understanding these limitations is essential for correctly interpreting the results.

## Data Limitations

### Selection Bias

**The `Fixes:` tag requirement creates systematic bias.**

Only bugs that were:
1. Recognized as bugs (not features or improvements)
2. Fixed with an explicit `Fixes:` tag
3. Committed to mainline (not just stable branches)

...are included in our dataset.

**What's missing**:
- Bugs fixed without `Fixes:` tags (~30% of security fixes, estimated)
- Bugs fixed only in stable branches without mainline backport
- "Silent fixes" where the fixer didn't realize it was a bug
- Bugs still unfixed

**Implication**: Our findings describe *recognized and documented* bugs, which may differ from the full population of bugs.

### Temporal Bias

**The `Fixes:` tag convention was adopted in 2013.**

Pre-2013 data is sparse and likely unrepresentative. Developers retroactively added some tags, but coverage is inconsistent.

| Period | Coverage | Notes |
|--------|----------|-------|
| 2004-2010 | Poor | Very few tags, mostly added retroactively |
| 2011-2013 | Moderate | Tag adoption increasing |
| 2014-present | Good | Standard practice |

**Implication**: Trend analyses should be interpreted cautiously for early years.

### Right-Censoring

**Recent bugs haven't had time to be fixed.**

A bug introduced in 2024 might take 3 years to fix, but we can only observe it if it's already been fixed. This biases recent data toward shorter-lived bugs.

**Mitigation**: We exclude the most recent year from some analyses, or note the potential bias.

### Attribution Uncertainty

**Reviewer information is inconsistently available.**

| Tag | Meaning | Availability |
|-----|---------|--------------|
| `Reviewed-by:` | Formal code review | ~40% of commits |
| `Acked-by:` | Maintainer approval | ~30% of commits |
| `Signed-off-by:` | DCO certification | ~99% of commits |

We use the first available in priority order, but `Signed-off-by` often just indicates the author, not a true reviewer.

**Implication**: Super-reviewer analysis is based on a subset of commits with clear reviewer attribution.

## Methodological Limitations

### Security Classification

**Our keyword-based approach is imprecise.**

Estimated performance:
- **Precision**: ~85% (some false positives)
- **Recall**: ~60% (many false negatives)

The actual number of security bugs is likely **higher** than we report.

### Causal Claims

**This is observational data. Correlation ≠ causation.**

We observe that:
- Super-reviewers are associated with faster bug fixes
- Weekend commits are associated with longer bug lifetimes

We **cannot** conclude that:
- Super-reviewers *cause* faster fixes (vs. working on simpler bugs)
- Weekends *cause* bugs to survive longer (vs. confounding factors)

Plausible confounders:
- Super-reviewers may select for certain subsystems or bug types
- Weekend commits may be from different developer populations
- Subsystem complexity correlates with both bug type and lifetime

### Subsystem Boundaries

**Kernel subsystem boundaries are fuzzy.**

Our file-path-based classification is a simplification:
- Some files belong to multiple logical subsystems
- Subsystem organization has changed over time
- Driver boundaries are particularly complex

### Bug Type Classification

**Bug type heuristics are noisy.**

We classify based on keywords like "use-after-free", "race condition", etc. But:
- Not all bugs are labeled
- Some labels are inaccurate
- Novel bug types may be missed

## Scope Limitations

### Linux-Specific

**Findings may not generalize to other codebases.**

The Linux kernel has unique characteristics:
- Very large codebase (~30M LOC)
- Mature development process with extensive review
- C-only (no memory safety from language features)
- Long-term support requirements

Findings about bug lifetimes, reviewer effectiveness, etc. may differ for:
- Smaller projects
- Projects in memory-safe languages
- Projects with different release cycles

### Historical Context

**Development practices have changed.**

What was true in 2010 may not be true in 2024:
- Testing tools have improved (Coverity, Syzkaller, etc.)
- CI/CD adoption has increased
- Developer population has changed
- Code review tools have evolved

Time series trends reflect this evolution, not just inherent bug dynamics.

## Interpretation Guidance

### What We Can Say

✅ "In our dataset of documented bug fixes, the median lifetime was 2.1 years"  
✅ "Developers with 50+ reviews are associated with 47% shorter bug lifetimes"  
✅ "Commits authored on weekends have longer median bug lifetimes"  

### What We Cannot Say

❌ "The average kernel bug survives 2.1 years" (selection bias)  
❌ "Expert reviewers prevent long-lived bugs" (causation unclear)  
❌ "Don't commit code on weekends" (confounders not controlled)  

### Recommended Citations

When citing this work, please include appropriate caveats:

> "Analysis of 125,000+ documented kernel bug fixes suggests that security bugs survive a median of 2.1 years, though this may underestimate actual bug lifetimes due to selection bias in the `Fixes:` tag convention."

## Future Work

These limitations suggest directions for improvement:

1. **Broader coverage**: Include bugs from stable branches, vendor kernels
2. **Ground truth validation**: Manual labeling of random sample for precision/recall estimation
3. **Causal inference**: Natural experiments (e.g., reviewer changes) for causal claims
4. **Cross-project comparison**: Apply methodology to other large C projects
5. **Longitudinal tracking**: Study how individual bugs evolve through multiple fixes

## Acknowledgments

We thank reviewers who pointed out several of these limitations during peer review. Honest assessment of limitations is essential for scientific integrity.
