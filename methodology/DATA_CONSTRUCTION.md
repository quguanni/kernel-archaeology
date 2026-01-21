# Dataset Construction

This document describes how the Linux kernel bug-fix pairs dataset was constructed, including data sources, extraction methods, and validation.

## Overview

The dataset consists of 125,000+ pairs of (buggy_commit, fix_commit) from the Linux kernel git repository, spanning 2004-2024.

**Data source**: Official Linux kernel git repository  
**Extraction method**: Parsing `Fixes:` tags from commit messages  
**HuggingFace**: [quguanni/linux-kernel-bugfix-pairs](https://huggingface.co/datasets/quguanni/linux-kernel-bugfix-pairs)

## The `Fixes:` Tag Convention

Since 2013, the Linux kernel community has standardized the use of `Fixes:` tags to link fix commits back to the original buggy commits:

```
commit abc123...
Author: Developer Name <dev@example.com>
Date:   Mon Jan 15 10:30:00 2024 +0000

    net: fix use-after-free in packet handling
    
    The previous implementation could access freed memory when...
    
    Fixes: def456... ("net: add new packet handler")
    Signed-off-by: Developer Name <dev@example.com>
```

This creates an explicit link between the fix and the bug it addresses.

## Extraction Pipeline

### Step 1: Clone and parse

```bash
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
```

```python
# Pseudocode for extraction
for commit in git_log():
    if "Fixes:" in commit.message:
        buggy_hash = extract_fixes_tag(commit.message)
        if buggy_hash and commit_exists(buggy_hash):
            yield BugFixPair(
                fix_commit=commit,
                buggy_commit=get_commit(buggy_hash)
            )
```

### Step 2: Metadata extraction

For each pair, we extract:

| Field | Source | Notes |
|-------|--------|-------|
| `buggy_commit_hash` | `Fixes:` tag | Full 40-char SHA |
| `fix_commit_hash` | Fix commit | Full 40-char SHA |
| `buggy_date` | `git show --format=%ai` | Author date, ISO format |
| `fix_date` | `git show --format=%ai` | Author date, ISO format |
| `buggy_author` | `git show --format=%an` | Author name |
| `fix_author` | `git show --format=%an` | Author name |
| `reviewer` | Commit message parsing | First Reviewed-by/Acked-by/Signed-off-by |
| `subsystem` | File path analysis | Dominant subsystem by lines changed |
| `files_changed` | `git diff --name-only` | List of modified files |
| `insertions` | `git diff --stat` | Lines added |
| `deletions` | `git diff --stat` | Lines removed |

### Step 3: Enrichment

Additional computed fields:

| Field | Computation |
|-------|-------------|
| `lifetime_days` | `fix_date - buggy_date` in days |
| `is_security` | Keyword matching on commit message |
| `bug_type` | Heuristic classification (UAF, race, overflow, etc.) |
| `fix_complexity` | `insertions + deletions` |

### Step 4: Validation and cleaning

**Removed records**:
- Invalid `Fixes:` tags (non-existent commits): ~2%
- Negative lifetimes (tag errors or rebasing artifacts): ~0.5%
- Commits before 2005 (unreliable tagging): ~1%
- Merge commits: ~0.3%

**Total after cleaning**: 125,847 bug-fix pairs

## Data Quality Assessment

### Sampling validation

We manually reviewed 500 randomly sampled pairs to assess quality:

| Metric | Value |
|--------|-------|
| Valid bug-fix relationship | 97.2% |
| Correct author attribution | 99.4% |
| Correct date extraction | 99.8% |
| Subsystem assignment accuracy | 94.6% |

### Known limitations

1. **Selection bias**: Only bugs with `Fixes:` tags are included. Bugs fixed without this tag are missed.

2. **Historical bias**: `Fixes:` tag adoption increased over time. Pre-2013 data is sparser.

3. **Right-censoring**: Recent bugs may not have been fixed yet, biasing recent years toward shorter-lived bugs.

4. **Attribution uncertainty**: Reviewer tags are inconsistently used; ~30% of commits lack explicit reviewer attribution.

### Coverage estimation

Based on comparison with CVE database:
- ~70% of known kernel CVEs from 2015-2023 have corresponding entries in our dataset
- Missing CVEs are typically fixed without `Fixes:` tags or in stable branches

## File Format

The dataset is provided in Parquet format for efficiency:

```python
import pandas as pd
df = pd.read_parquet("kernel_bugfix_pairs.parquet")
```

### Schema

```
buggy_commit_hash: string (40 chars)
fix_commit_hash: string (40 chars)  
buggy_date: datetime64[ns]
fix_date: datetime64[ns]
lifetime_days: int64
buggy_author: string
fix_author: string
reviewer: string (nullable)
subsystem: string
files_changed: list[string]
insertions: int64
deletions: int64
is_security: bool
bug_type: string (nullable)
commit_message: string (truncated to 1000 chars)
```

### Size

- Rows: 125,847
- Parquet file: ~45 MB
- CSV equivalent: ~180 MB

## Reproducibility

To reproduce the dataset from scratch:

```bash
# 1. Clone the extraction code
git clone https://github.com/quguanni/kernel-bugfix-extractor.git
cd kernel-bugfix-extractor

# 2. Clone Linux kernel (warning: ~4GB)
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

# 3. Run extraction
python extract_bugfix_pairs.py --kernel-path ./linux --output ./data

# 4. Run enrichment
python enrich_dataset.py --input ./data/raw_pairs.parquet --output ./data/kernel_bugfix_pairs.parquet
```

Expected runtime: ~2 hours on modern hardware.

## Updates

The dataset will be updated quarterly to include new bug fixes. Version history:

| Version | Date | Records | Notes |
|---------|------|---------|-------|
| v1.0.0 | 2025-01 | 125,847 | Initial release |

## Acknowledgments

- The Linux kernel community for adopting the `Fixes:` tag convention
- Greg Kroah-Hartman for advocating stable backport documentation
- LWN.net for historical context on kernel development practices
