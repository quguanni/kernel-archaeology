#!/usr/bin/env python3
"""
Analyze vulnerability introduction RATES in the Linux kernel.

Computes the rate of vulnerable commits (vulnerabilities / total commits)
across different dimensions: hour of day, day of week, month, and year.
This is more informative than raw counts since it normalizes for activity levels.

Usage:
    # First extract total commits:
    cd /path/to/linux
    git log --format="%ai|%ae" --since="2005-01-01" > total_commits.csv

    # Then analyze:
    python analyze_vuln_rate.py --commits total_commits.csv
    python analyze_vuln_rate.py --commits total_commits.csv --output figures/
"""

import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datasets import load_dataset

plt.style.use('seaborn-v0_8-whitegrid')

DOW_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def load_total_commits(path: Path) -> pd.DataFrame:
    """Load total commits from git log output."""
    commits = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if '|' in line:
                parts = line.strip().split('|', 1)
                if len(parts) >= 1:
                    try:
                        dt = pd.to_datetime(parts[0])
                        commits.append({
                            'hour': dt.hour,
                            'dow': dt.dayofweek,
                            'month': dt.month,
                            'year': dt.year
                        })
                    except:
                        pass
    
    return pd.DataFrame(commits)


def load_vuln_commits() -> pd.DataFrame:
    """Load vulnerability dataset from HuggingFace."""
    ds = load_dataset("pebblebed/kernel-vuln-dataset", split="train")
    df = pd.DataFrame(ds)
    
    df['intro_date'] = pd.to_datetime(df['introducing_date'], errors='coerce', utc=True)
    df['hour'] = df['intro_date'].dt.hour
    df['dow'] = df['intro_date'].dt.dayofweek
    df['month'] = df['intro_date'].dt.month
    df['year'] = df['intro_date'].dt.year
    
    return df


def compute_rates(total_df: pd.DataFrame, vuln_df: pd.DataFrame) -> dict:
    """Compute vulnerability rates across dimensions."""
    rates = {}
    
    # By hour
    hour_total = total_df.groupby('hour').size()
    hour_vuln = vuln_df.groupby('hour').size()
    rates['hour'] = (hour_vuln / hour_total * 100).fillna(0)
    
    # By day of week
    dow_total = total_df.groupby('dow').size()
    dow_vuln = vuln_df.groupby('dow').size()
    rates['dow'] = (dow_vuln / dow_total * 100).fillna(0)
    
    # By month
    month_total = total_df.groupby('month').size()
    month_vuln = vuln_df.groupby('month').size()
    rates['month'] = (month_vuln / month_total * 100).fillna(0)
    
    # Weekend vs weekday
    weekday_total = total_df[total_df['dow'] < 5].shape[0]
    weekend_total = total_df[total_df['dow'] >= 5].shape[0]
    weekday_vuln = vuln_df[vuln_df['dow'] < 5].shape[0]
    weekend_vuln = vuln_df[vuln_df['dow'] >= 5].shape[0]
    
    rates['weekday'] = weekday_vuln / weekday_total * 100
    rates['weekend'] = weekend_vuln / weekend_total * 100
    rates['overall'] = len(vuln_df) / len(total_df) * 100
    
    return rates


def plot_rate_analysis(rates: dict, total_count: int, vuln_count: int, output_dir: Path):
    """Generate rate analysis visualizations."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Kernel Vulnerability Introduction Rate\n'
                 f'({vuln_count:,} vulnerabilities / {total_count:,} commits = {rates["overall"]:.2f}%)',
                 fontsize=14, fontweight='bold')
    
    # By hour
    ax = axes[0, 0]
    hour_rate = rates['hour']
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(hour_rate)))
    sorted_idx = np.argsort(hour_rate.values)
    bar_colors = [colors[list(sorted_idx).index(i)] for i in range(len(hour_rate))]
    ax.bar(hour_rate.index, hour_rate.values, color=bar_colors, edgecolor='white')
    ax.axhline(hour_rate.mean(), color='red', linestyle='--', lw=2, 
               label=f'Mean: {hour_rate.mean():.2f}%')
    ax.set_xlabel('Hour (UTC)')
    ax.set_ylabel('Vulnerability Rate (%)')
    ax.set_title('By Hour of Day')
    ax.legend()
    
    # By day of week
    ax = axes[0, 1]
    dow_rate = rates['dow']
    colors = ['#2ecc71' if i < 5 else '#e74c3c' for i in range(7)]
    ax.bar(range(7), [dow_rate.get(i, 0) for i in range(7)], color=colors, edgecolor='white')
    ax.set_xticks(range(7))
    ax.set_xticklabels(DOW_NAMES)
    ax.axhline(rates['weekday'], color='#2ecc71', linestyle='--', lw=2,
               label=f'Weekday: {rates["weekday"]:.2f}%')
    ax.axhline(rates['weekend'], color='#e74c3c', linestyle='--', lw=2,
               label=f'Weekend: {rates["weekend"]:.2f}%')
    ax.set_xlabel('Day of Week')
    ax.set_ylabel('Vulnerability Rate (%)')
    ax.set_title('By Day of Week')
    ax.legend()
    
    # By month
    ax = axes[1, 0]
    month_rate = rates['month']
    month_values = [month_rate.get(i, 0) for i in range(1, 13)]
    ax.bar(range(12), month_values, color='steelblue', edgecolor='white')
    ax.set_xticks(range(12))
    ax.set_xticklabels(MONTH_NAMES)
    ax.axhline(np.mean(month_values), color='red', linestyle='--', lw=2,
               label=f'Mean: {np.mean(month_values):.2f}%')
    ax.set_xlabel('Month')
    ax.set_ylabel('Vulnerability Rate (%)')
    ax.set_title('By Month')
    ax.legend()
    
    # Summary
    ax = axes[1, 1]
    ax.axis('off')
    
    summary = f"""
    VULNERABILITY RATE ANALYSIS
    {'='*40}
    
    Total commits:        {total_count:>12,}
    Vulnerable commits:   {vuln_count:>12,}
    Overall rate:         {rates['overall']:>11.2f}%
    
    By Day of Week:
      Weekday average:    {rates['weekday']:>11.2f}%
      Weekend average:    {rates['weekend']:>11.2f}%
      Difference:         {rates['weekend'] - rates['weekday']:>+10.2f}%
    
    By Hour (UTC):
      Peak: {int(rates['hour'].idxmax()):02d}:00 ({rates['hour'].max():.2f}%)
      Low:  {int(rates['hour'].idxmin()):02d}:00 ({rates['hour'].min():.2f}%)
    """
    
    ax.text(0.1, 0.9, summary, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'vuln_rate_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_dir / 'vuln_rate_analysis.png'}")
    
    # Weekend focus plot
    fig, ax = plt.subplots(figsize=(10, 6))
    dow_rate = rates['dow']
    colors = ['#2ecc71' if i < 5 else '#e74c3c' for i in range(7)]
    bars = ax.bar(range(7), [dow_rate.get(i, 0) for i in range(7)], 
                  color=colors, edgecolor='black')
    
    ax.set_xticks(range(7))
    ax.set_xticklabels(DOW_NAMES, fontsize=12)
    ax.set_xlabel('Day of Week', fontsize=12)
    ax.set_ylabel('Vulnerability Rate (%)', fontsize=12)
    
    weekend_safer = rates['weekend'] < rates['weekday']
    if weekend_safer:
        title = 'Weekend Commits Have LOWER Vulnerability Rate'
    else:
        title = 'Weekend Commits Have HIGHER Vulnerability Rate'
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.axhline(rates['weekday'], color='#2ecc71', linestyle='--', lw=2,
               label=f'Weekday: {rates["weekday"]:.2f}%')
    ax.axhline(rates['weekend'], color='#e74c3c', linestyle='--', lw=2,
               label=f'Weekend: {rates["weekend"]:.2f}%')
    
    for i, v in enumerate([dow_rate.get(i, 0) for i in range(7)]):
        ax.text(i, v + 0.1, f'{v:.2f}%', ha='center', fontsize=10, fontweight='bold')
    
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(output_dir / 'vuln_rate_weekend.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_dir / 'vuln_rate_weekend.png'}")


def print_report(rates: dict, total_count: int, vuln_count: int):
    """Print rate analysis report."""
    print("=" * 60)
    print("VULNERABILITY RATE ANALYSIS")
    print("=" * 60)
    
    print(f"\nTotal commits:      {total_count:>12,}")
    print(f"Vulnerable commits: {vuln_count:>12,}")
    print(f"Overall rate:       {rates['overall']:>11.2f}%")
    
    print(f"\nBy Day of Week:")
    print(f"  Weekday average:  {rates['weekday']:.2f}%")
    print(f"  Weekend average:  {rates['weekend']:.2f}%")
    
    if rates['weekend'] < rates['weekday']:
        print(f"  → Weekend is {rates['weekday']/rates['weekend']:.2f}x SAFER")
    else:
        print(f"  → Weekend is {rates['weekend']/rates['weekday']:.2f}x RISKIER")
    
    print(f"\nBy Hour (UTC):")
    print(f"  Peak: {int(rates['hour'].idxmax()):02d}:00 ({rates['hour'].max():.2f}%)")
    print(f"  Low:  {int(rates['hour'].idxmin()):02d}:00 ({rates['hour'].min():.2f}%)")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Analyze vulnerability introduction rates")
    parser.add_argument('--commits', '-c', type=Path, required=True,
                        help='Git log output (date|email format)')
    parser.add_argument('--output', '-o', type=Path, default=Path('.'),
                        help='Output directory for plots')
    args = parser.parse_args()
    
    print("Loading total commits...")
    total_df = load_total_commits(args.commits)
    print(f"Loaded {len(total_df):,} total commits")
    
    print("Loading vulnerability dataset...")
    vuln_df = load_vuln_commits()
    print(f"Loaded {len(vuln_df):,} vulnerable commits")
    
    print("Computing rates...")
    rates = compute_rates(total_df, vuln_df)
    
    print_report(rates, len(total_df), len(vuln_df))
    
    print(f"\nGenerating plots...")
    plot_rate_analysis(rates, len(total_df), len(vuln_df), args.output)
    
    print("Done.")


if __name__ == "__main__":
    main()
