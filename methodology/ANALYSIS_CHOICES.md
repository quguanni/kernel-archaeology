# Analysis Choices

Key analytical decisions and their rationale.

## Super-Reviewer Threshold: 50+ Fixes

Developers with 50+ bug fix reviews qualify as "super-reviewers."

- **Why 50?** Statistical power—below this, you can't distinguish skill from luck with 95% confidence.
- **Sensitivity:** Tested thresholds 20-100. The 47% speedup finding holds across this range (42-51%).

## Bug Lifetime Calculation

`lifetime_days = fix_date - introducing_date`

- Dates from git commit metadata, normalized to UTC
- Negative lifetimes excluded (indicate `Fixes:` tag errors)
- Same-day fixes counted as 0 days

## Subsystem Assignment

Assigned based on file paths in the fix commit, weighted by lines changed.

```
net/      → networking
fs/       → filesystems  
drivers/  → drivers
mm/       → memory management
kernel/   → core kernel
```

Cross-subsystem commits assigned to the subsystem with most changed lines.

## Security Classification

Keyword-based heuristics in commit messages:
- Explicit: `CVE`, `security`, `vulnerability`
- Bug types: `use-after-free`, `buffer overflow`, `race condition`

**Estimated precision:** ~85% | **Estimated recall:** ~60%

We likely *undercount* security bugs.

## Weekend Definition

Commits authored on Saturday or Sunday (UTC). Author date used, not committer date.

## Statistical Tests

- **Mann-Whitney U:** Lifetime comparisons (non-parametric, handles skew)
- **Significance:** p < 0.05 with Bonferroni correction for multiple comparisons

## Data Exclusions

- Commits before 2005-01-01 (unreliable `Fixes:` tag usage)
- Merge commits
- Invalid dates or non-existent referenced commits
