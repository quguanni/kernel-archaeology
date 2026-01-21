#!/usr/bin/env python3
"""
Analyze the Linux kernel vulnerability dataset.

This script loads the pebblebed/kernel-vuln-dataset from HuggingFace and
computes summary statistics on vulnerability lifetimes, subsystems, bug types,
and temporal patterns.

Usage:
    python analyze_vuln_db.py
    python analyze_vuln_db.py --output results/
"""

import argparse
from pathlib import Path
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt
from datasets import load_dataset

plt.style.use('seaborn-v0_8-whitegrid')


def load_vuln_dataset() -> pd.DataFrame:
    """Load vulnerability dataset from HuggingFace."""
    ds = load_dataset("pebblebed/kernel-vuln-dataset", split="train")
    df = pd.DataFrame(ds)
    
    # Parse dates
    df['intro_date'] = pd.to_datetime(df['introducing_date'], errors='coerce', utc=True)
    df['fix_date'] = pd.to_datetime(df['fixing_date'], errors='coerce', utc=True)
    
    return df


def compute_lifetime_stats(df: pd.DataFrame) -> dict:
    """Compute vulnerability lifetime statistics."""
    lifetime = df['lifetime_days'].dropna()
    
    return {
        'count': len(lifetime),
        'mean_days': lifetime.mean(),
        'mean_years': lifetime.mean() / 365,
        'median_days': lifetime.median(),
        'median_years': lifetime.median() / 365,
        'max_days': lifetime.max(),
        'max_years': lifetime.max() / 365,
        'percentiles': {p: lifetime.quantile(p/100) for p in [25, 50, 75, 90, 95, 99]}
    }


def compute_subsystem_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-subsystem vulnerability statistics."""
    stats = df.groupby('subsystem').agg({
        'lifetime_days': ['count', 'mean', 'median'],
        'fixing_commit': 'count'
    }).reset_index()
    
    stats.columns = ['subsystem', 'count', 'mean_lifetime', 'median_lifetime', 'fixes']
    stats = stats.sort_values('count', ascending=False)
    
    return stats


def compute_bugtype_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-bug-type statistics."""
    stats = df.groupby('bug_type').agg({
        'lifetime_days': ['count', 'mean', 'median']
    }).reset_index()
    
    stats.columns = ['bug_type', 'count', 'mean_lifetime', 'median_lifetime']
    stats = stats.sort_values('count', ascending=False)
    
    return stats


def compute_temporal_stats(df: pd.DataFrame) -> dict:
    """Compute temporal patterns in vulnerability introduction."""
    df = df.copy()
    df['intro_year'] = df['intro_date'].dt.year
    df['intro_month'] = df['intro_date'].dt.month
    df['intro_dow'] = df['intro_date'].dt.dayofweek
    
    return {
        'by_year': df['intro_year'].value_counts().sort_index(),
        'by_month': df['intro_month'].value_counts().sort_index(),
        'by_dow': df['intro_dow'].value_counts().sort_index(),
    }


def generate_plots(df: pd.DataFrame, output_dir: Path):
    """Generate analysis visualizations."""
    output_dir.mkdir(parents=True, exist_ok=True)
    lifetime = df['lifetime_days'].dropna()
    
    # Figure 1: Overview (2x2)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Lifetime distribution
    ax = axes[0, 0]
    ax.hist(lifetime[lifetime < 3000], bins=50, color='steelblue', edgecolor='white', alpha=0.8)
    ax.axvline(lifetime.mean(), color='red', linestyle='--', lw=2, label=f'Mean: {lifetime.mean():.0f}d')
    ax.axvline(lifetime.median(), color='orange', linestyle='--', lw=2, label=f'Median: {lifetime.median():.0f}d')
    ax.set_xlabel('Lifetime (days)')
    ax.set_ylabel('Count')
    ax.set_title('Vulnerability Lifetime Distribution')
    ax.legend()
    
    # By year
    ax = axes[0, 1]
    yearly = df.groupby(df['intro_date'].dt.year).size()
    yearly = yearly[yearly.index >= 2010]
    ax.bar(yearly.index.astype(int), yearly.values, color='steelblue', edgecolor='white')
    ax.set_xlabel('Year')
    ax.set_ylabel('Vulnerabilities Introduced')
    ax.set_title('Vulnerabilities by Year Introduced')
    
    # By subsystem
    ax = axes[1, 0]
    subsystem_counts = df['subsystem'].value_counts().head(10)
    ax.barh(subsystem_counts.index, subsystem_counts.values, color='steelblue', edgecolor='white')
    ax.set_xlabel('Count')
    ax.set_title('Top 10 Subsystems')
    ax.invert_yaxis()
    
    # By bug type
    ax = axes[1, 1]
    bugtype_counts = df['bug_type'].value_counts().head(10)
    ax.barh(bugtype_counts.index, bugtype_counts.values, color='coral', edgecolor='white')
    ax.set_xlabel('Count')
    ax.set_title('Top 10 Bug Types')
    ax.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'vulnerability_overview.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 2: Lifetime by subsystem
    fig, ax = plt.subplots(figsize=(12, 6))
    subsystem_lifetime = df.groupby('subsystem')['lifetime_days'].median().sort_values(ascending=False).head(15)
    ax.barh(subsystem_lifetime.index, subsystem_lifetime.values, color='forestgreen', edgecolor='white')
    ax.set_xlabel('Median Lifetime (days)')
    ax.set_title('Vulnerability Lifetime by Subsystem')
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_dir / 'lifetime_by_subsystem.png', dpi=150, bbox_inches='tight')
    plt.close()


def print_report(df: pd.DataFrame, lifetime_stats: dict, subsystem_stats: pd.DataFrame, 
                 bugtype_stats: pd.DataFrame):
    """Print summary report to stdout."""
    print("=" * 70)
    print("LINUX KERNEL VULNERABILITY ANALYSIS")
    print("=" * 70)
    
    print(f"\nDataset: {len(df):,} vulnerability-fixing commits")
    print(f"With CVE IDs: {df['cve_id'].notna().sum():,} ({100*df['cve_id'].notna().mean():.1f}%)")
    
    print(f"\n{'LIFETIME STATISTICS':=^70}")
    print(f"  Mean:   {lifetime_stats['mean_days']:.0f} days ({lifetime_stats['mean_years']:.1f} years)")
    print(f"  Median: {lifetime_stats['median_days']:.0f} days ({lifetime_stats['median_years']:.1f} years)")
    print(f"  Max:    {lifetime_stats['max_days']:.0f} days ({lifetime_stats['max_years']:.1f} years)")
    
    print(f"\n  Percentiles:")
    for p, val in lifetime_stats['percentiles'].items():
        print(f"    {p}th: {val:.0f} days ({val/365:.1f} years)")
    
    print(f"\n{'TOP SUBSYSTEMS':=^70}")
    for _, row in subsystem_stats.head(10).iterrows():
        print(f"  {row['subsystem']:<25} {row['count']:>6,} vulns, {row['mean_lifetime']:>6.0f}d avg")
    
    print(f"\n{'TOP BUG TYPES':=^70}")
    for _, row in bugtype_stats.head(10).iterrows():
        print(f"  {row['bug_type']:<25} {row['count']:>6,} vulns, {row['mean_lifetime']:>6.0f}d avg")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Analyze Linux kernel vulnerability dataset")
    parser.add_argument('--output', '-o', type=Path, default=Path('.'),
                        help='Output directory for plots')
    args = parser.parse_args()
    
    print("Loading dataset from HuggingFace...")
    df = load_vuln_dataset()
    
    print("Computing statistics...")
    lifetime_stats = compute_lifetime_stats(df)
    subsystem_stats = compute_subsystem_stats(df)
    bugtype_stats = compute_bugtype_stats(df)
    
    print_report(df, lifetime_stats, subsystem_stats, bugtype_stats)
    
    print(f"\nGenerating plots in {args.output}/...")
    generate_plots(df, args.output)
    
    print("Done.")


if __name__ == "__main__":
    main()
