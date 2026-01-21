# Analysis Choices

This document explains the reasoning behind key analytical decisions in this study. These choices affect reproducibility and interpretation of results.

## Super-Reviewer Threshold (50+ fixes)

**Choice**: We define "super-reviewers" as developers who have reviewed at least 50 bug fixes.

**Rationale**: 
- **Statistical power**: With fewer samples, you can't distinguish skill from luck. At n=50, we have 95% confidence that observed differences reflect real effects.
- **Stability**: Median lifetime estimates stabilize around n=30-40 samples. We chose 50 for additional margin.
- **Alternative considered**: 25 fixes (used in some prior work). This yields more super-reviewers but with less reliable individual estimates.

**Sensitivity analysis**: We tested thresholds from 20 to 100. The 47% speedup finding is robust across this range (varies from 42% at n=20 to 51% at n=100).

## Security Bug Classification

**Choice**: We classify bugs as "security-relevant" based on keyword heuristics in commit messages.

**Keywords used**:
- Explicit: `CVE`, `security`, `vulnerability`, `exploit`
- Bug types: `use-after-free`, `double-free`, `buffer overflow`, `integer overflow`, `null pointer dereference`, `memory leak` (when combined with security context)
- CWE patterns: References to CWE-xxx identifiers

**Rationale**:
- Manual labeling of 125K commits is infeasible
- Keyword-based classification is reproducible and transparent
- We likely **undercount** security bugs (not all security fixes mention these keywords)

**Limitations**:
- False negatives: Security fixes without explicit keywords are missed
- False positives: Some keyword matches may not be security-relevant
- Estimated precision: ~85% (based on manual review of 200 samples)
- Estimated recall: ~60% (based on known CVEs in our dataset)

## Subsystem Assignment

**Choice**: Bugs are assigned to the subsystem with the most changed lines in the fix commit.

**Rationale**:
- File paths reliably indicate subsystem (e.g., `net/` → networking)
- Weighting by lines changed handles cross-subsystem commits
- Single assignment simplifies analysis (vs. multi-label)

**Alternatives considered**:
1. **First file touched**: Arbitrary, doesn't reflect importance
2. **Multi-label**: More accurate but complicates statistics
3. **MAINTAINERS file**: Would require historical MAINTAINERS versions

**Subsystem categories**:
```
drivers/     → drivers (further subdivided by type)
net/         → networking  
fs/          → filesystems
mm/          → memory management
kernel/      → core kernel
arch/        → architecture-specific
sound/       → sound subsystem
crypto/      → cryptography
security/    → security modules (LSM, etc.)
...
```

## Bug Lifetime Calculation

**Choice**: Lifetime = `fix_date - buggy_date` in days

**Considerations**:
- **Fix date**: Date the fix was committed to mainline (not when patch was written)
- **Buggy date**: Date the buggy commit was introduced (from `Fixes:` tag)
- **Time zone handling**: All dates normalized to UTC

**Edge cases**:
- Same-day fixes: Counted as 0 days (not excluded)
- Negative lifetimes: Excluded (indicate `Fixes:` tag errors)
- Missing dates: Excluded from analysis

## Temporal Grouping

**Choice**: Primary analysis uses yearly grouping; quarterly for detailed trends.

**Rationale**:
- Yearly: Sufficient data points per bin, clear long-term trends
- Quarterly: Reveals seasonal patterns (conference deadlines, release cycles)

**Known artifacts**:
- Early years (2004-2007): Fewer `Fixes:` tags used, potential undercount
- Recent years (2023-2024): Bugs may not have been fixed yet (right-censoring)

## Weekend Effect Definition

**Choice**: "Weekend commits" are those authored on Saturday or Sunday (local time where available, UTC otherwise).

**Rationale**:
- Author date better reflects when code was written (vs. committer date)
- Weekend work patterns differ across time zones but UTC provides consistent baseline

**Confounds**:
- Time zone misattribution may affect some commits
- Some developers may work weekends professionally (not "side project" pattern)

## Statistical Tests

**Tests used**:
- **Mann-Whitney U**: Comparing lifetime distributions (non-parametric, handles skew)
- **Pearson correlation**: Temporal trends
- **Chi-squared**: Categorical comparisons (subsystem × security)

**Why not t-tests?**
Bug lifetimes are heavily right-skewed. Log-transformation helps but Mann-Whitney is more robust.

**Significance threshold**: p < 0.05 for all reported findings, with Bonferroni correction for multiple comparisons where applicable.

## Data Quality Decisions

### Excluded commits
- Commits before 2005-01-01 (unreliable `Fixes:` tag usage)
- Merge commits
- Commits with invalid dates
- Commits where `Fixes:` tag points to non-existent commit

### Handling duplicates
Some bugs are fixed multiple times (incomplete initial fix). We keep only the first fix unless specifically analyzing fix quality.

### Author/reviewer attribution
- Author: From commit `Author:` field
- Reviewer: Extracted from `Reviewed-by:`, `Acked-by:`, `Signed-off-by:` tags (in that priority order)
- Some commits have multiple reviewers; we use the first listed

## Reproducibility Notes

To reproduce our exact results:
1. Use the dataset version tagged `v1.0.0` on HuggingFace
2. Set random seed to 42 for any sampling operations
3. Use Python 3.10+ with package versions in `requirements.txt`

Known non-determinism:
- Floating-point operations may differ slightly across architectures
- Plot aesthetics may vary with matplotlib versions
