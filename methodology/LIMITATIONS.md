# Limitations

Honest assessment of what this analysis does and doesn't capture.

## Selection Bias

**The `Fixes:` tag requirement creates systematic bias.**

Only bugs that were (1) recognized as bugs, (2) fixed with an explicit `Fixes:` tag, and (3) committed to mainline are included.

**Missing:** ~30% of security fixes lack `Fixes:` tags, bugs in stable-only branches, silent fixes, unfixed bugs.

## Temporal Bias

**The `Fixes:` tag convention was adopted ~2013.**

| Period | Coverage |
|--------|----------|
| 2005-2010 | Poor (sparse, mostly retroactive) |
| 2011-2013 | Moderate |
| 2014+ | Good (standard practice) |

Early-year trends should be interpreted cautiously.

## Right-Censoring

**Recent bugs haven't had time to be fixed.**

A bug introduced in 2024 might take years to fix. This biases recent data toward shorter-lived bugs.

## Causal Claims

**This is observational data. Correlation ≠ causation.**

We observe associations (super-reviewers ↔ faster fixes, weekends ↔ longer lifetimes) but cannot prove causation. Confounders exist.

## What We Can Say

✅ "In documented bug fixes, median lifetime was 2.1 years"  
✅ "Developers with 50+ reviews are associated with 47% shorter lifetimes"

## What We Cannot Say

❌ "The average kernel bug survives 2.1 years" (selection bias)  
❌ "Expert reviewers prevent long-lived bugs" (causation unclear)  
❌ "Don't commit on weekends" (confounders not controlled)

## Linux-Specific

Findings may not generalize. The kernel is uniquely large (~30M LOC), C-only, and has mature review processes.
