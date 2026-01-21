# Kernel Archaeology

**20 years of Linux kernel security bugs, analyzed.**

Reproducible analysis of 125,000+ kernel bug-fix pairs (2005-2025) and 1M+ commits to understand vulnerability patterns and corporate contributions.

## Key Findings

| Finding | Insight |
|---------|---------|
| **2.1 years** | Median bug survival time before fix |
| **117 super-reviewers** | Catch bugs 47% faster than average |
| **5x longer** | Race conditions survive vs other bug types |
| **45% longer** | Bug lifetime for weekend commits |

![Lifetime Distribution](figures/01_lifetime_distribution.png)

## Corporate Contributions

![Corporate Dashboard](figures/corporate_dashboard.png)

## Repository Structure

```
├── figures/                  # All visualizations (01-18, corporate_*, vuln_rate_*)
├── scripts/
│   ├── analyze_vuln_db.py        # Analyze HuggingFace vulnerability dataset
│   ├── analyze_vuln_rate.py      # Vulnerability rates normalized by commit volume
│   ├── cluster_vuln.py           # t-SNE/UMAP clustering
│   ├── corporate_contributions.py # Corporate contribution analysis
│   ├── visualize_corporate.py    # Corporate visualizations
│   └── mine_commits.sh           # Extract commits from git repo
├── methodology/
│   ├── ANALYSIS_CHOICES.md       # Analytical decisions explained
│   └── LIMITATIONS.md            # Honest limitations assessment
├── notebooks/
│   └── 01_data_exploration.ipynb
└── requirements.txt
```

## Quick Start

```bash
git clone https://github.com/quguanni/kernel-archaeology.git
cd kernel-archaeology
pip install -r requirements.txt

# Vulnerability analysis (loads from HuggingFace)
python scripts/analyze_vuln_db.py --output figures/

# Corporate contributions
./scripts/mine_commits.sh /path/to/linux > all_commits.csv
python scripts/corporate_contributions.py --data all_commits.csv --output results.csv --yearly yearly.csv
python scripts/visualize_corporate.py --results results.csv --yearly yearly.csv --output figures/
```

## Dataset

Available on HuggingFace: [pebblebed/kernel-vuln-dataset](https://huggingface.co/datasets/pebblebed/kernel-vuln-dataset)

**Key fields:** `fixing_commit`, `introducing_commit`, `lifetime_days`, `subsystem`, `bug_type`, `severity_hint`

## Methodology

- [ANALYSIS_CHOICES.md](methodology/ANALYSIS_CHOICES.md) — Thresholds, classifications, and statistical decisions
- [LIMITATIONS.md](methodology/LIMITATIONS.md) — Selection bias, temporal bias, and interpretation caveats

## Citation

```bibtex
@misc{qu2025kernel,
  author = {Qu, Jenny Guanni},
  title = {Kernel Archaeology},
  year = {2025},
  url = {https://github.com/quguanni/kernel-archaeology}
}
```

## License

Code: MIT | Data/Figures: CC-BY-4.0

## Contact

Jenny Guanni Qu · jenny@pebblebed.com · [Pebblebed Ventures](https://pebblebed.com)
