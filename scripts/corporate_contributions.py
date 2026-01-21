#!/usr/bin/env python3
"""
Analyze corporate contributions to the Linux kernel.

Classifies kernel commits by author email domain to estimate corporate
contributions. Note: This is a lower bound since many developers use
personal emails (gmail, kernel.org) even when employed by companies.

Usage:
    # First extract commits from kernel repo:
    cd /path/to/linux
    git log --format="%H|%ae|%ai|%s" --since="2005-01-01" > all_commits.csv

    # Then analyze:
    python corporate_contributions.py --data all_commits.csv
    python corporate_contributions.py --data all_commits.csv --output results.csv --yearly yearly.csv
"""

import argparse
from pathlib import Path
from collections import defaultdict

import pandas as pd

# Company email domain mappings
COMPANY_DOMAINS = {
    'Google': ['google.com', 'chromium.org', 'android.com'],
    'Intel': ['intel.com'],
    'Red Hat': ['redhat.com'],
    'Microsoft': ['microsoft.com', 'linux.microsoft.com'],
    'Meta': ['fb.com', 'facebook.com', 'meta.com'],
    'Amazon': ['amazon.com', 'aws.com'],
    'IBM': ['ibm.com', 'linux.ibm.com', 'linux.vnet.ibm.com'],
    'Samsung': ['samsung.com'],
    'Huawei': ['huawei.com', 'hisilicon.com'],
    'NVIDIA': ['nvidia.com', 'mellanox.com'],
    'AMD': ['amd.com'],
    'Oracle': ['oracle.com'],
    'Arm': ['arm.com'],
    'Qualcomm': ['quicinc.com', 'qualcomm.com', 'codeaurora.org'],
    'Broadcom': ['broadcom.com'],
    'SUSE': ['suse.com', 'suse.de', 'suse.cz'],
    'Canonical': ['canonical.com'],
    'Linaro': ['linaro.org'],
    'Linux Foundation': ['linuxfoundation.org'],
    'Cisco': ['cisco.com'],
    'VMware': ['vmware.com'],
    'Texas Instruments': ['ti.com'],
    'NXP': ['nxp.com'],
    'Renesas': ['renesas.com'],
    'Sony': ['sony.com'],
    'Collabora': ['collabora.com'],
    'Bootlin': ['bootlin.com', 'free-electrons.com'],
    'Linutronix': ['linutronix.de'],
    'Marvell': ['marvell.com', 'cavium.com'],
    'MediaTek': ['mediatek.com'],
    'Alibaba': ['alibaba-inc.com', 'linux.alibaba.com'],
    'Tencent': ['tencent.com'],
    'ByteDance': ['bytedance.com'],
}

# Build reverse lookup
DOMAIN_TO_COMPANY = {}
for company, domains in COMPANY_DOMAINS.items():
    for domain in domains:
        DOMAIN_TO_COMPANY[domain] = company

# Personal email domains
PERSONAL_DOMAINS = {'gmail.com', 'yahoo.com', 'hotmail.com', 'protonmail.com',
                    'kernel.org', 'ozlabs.org', 'infradead.org', 'lwn.net'}


def classify_email(email: str) -> str:
    """Classify email domain as company, independent, or unknown."""
    if pd.isna(email) or not email or '@' not in str(email):
        return 'Unknown'
    
    domain = str(email).lower().strip().split('@')[1]
    
    # Check exact match
    if domain in DOMAIN_TO_COMPANY:
        return DOMAIN_TO_COMPANY[domain]
    
    # Check subdomain match
    for known_domain, company in DOMAIN_TO_COMPANY.items():
        if domain.endswith('.' + known_domain):
            return company
    
    # Personal domains
    if domain in PERSONAL_DOMAINS:
        return 'Independent/Other'
    
    return 'Independent/Other'


def load_git_log(path: Path) -> pd.DataFrame:
    """Load git log output (pipe-delimited: hash|email|date|subject)."""
    return pd.read_csv(
        path, sep='|', header=None,
        names=['commit', 'email', 'date', 'subject'],
        on_bad_lines='skip',
        encoding='utf-8',
        encoding_errors='replace'
    )


def analyze_contributions(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Analyze contributions by company, returning totals and yearly breakdown."""
    df = df.copy()
    df['company'] = df['email'].apply(classify_email)
    df['date'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
    df['year'] = df['date'].dt.year
    
    # Total counts
    counts = df['company'].value_counts()
    total = len(df)
    
    results = pd.DataFrame({
        'company': counts.index,
        'commits': counts.values,
        'percentage': 100 * counts.values / total
    })
    
    # Yearly breakdown
    yearly = df.groupby(['year', 'company']).size().unstack(fill_value=0)
    
    return results, yearly


def print_report(results: pd.DataFrame, yearly: pd.DataFrame):
    """Print formatted analysis report."""
    print("=" * 70)
    print("CORPORATE CONTRIBUTIONS TO LINUX KERNEL")
    print("=" * 70)
    
    # Top companies
    known = results[~results['company'].isin(['Independent/Other', 'Unknown'])]
    known = known.sort_values('commits', ascending=False)
    
    print(f"\n{'Company':<25} {'Commits':>12} {'Percentage':>12}")
    print("-" * 50)
    for _, row in known.head(20).iterrows():
        print(f"{row['company']:<25} {row['commits']:>12,} {row['percentage']:>11.1f}%")
    
    # Summary
    total = results['commits'].sum()
    corporate = known['commits'].sum()
    independent = results.loc[results['company'] == 'Independent/Other', 'commits'].sum()
    
    print(f"\n{'SUMMARY':=^50}")
    print(f"Corporate (tracked):  {corporate:>12,} ({100*corporate/total:.1f}%)")
    print(f"Independent/Other:    {independent:>12,} ({100*independent/total:.1f}%)")
    print(f"Total:                {total:>12,}")
    
    # Recent years
    print(f"\n{'RECENT TRENDS':=^50}")
    for year in range(2020, 2026):
        if year not in yearly.index:
            continue
        year_data = yearly.loc[year].sort_values(ascending=False)
        year_data = year_data[~year_data.index.isin(['Independent/Other', 'Unknown'])]
        top3 = year_data.head(3)
        year_total = yearly.loc[year].sum()
        
        top3_str = ", ".join([f"{c} ({100*v/year_total:.1f}%)" for c, v in top3.items()])
        print(f"{year}: {top3_str}")
    
    print("\n" + "=" * 70)
    print("NOTE: Corporate percentages are LOWER BOUNDS.")
    print("Many developers use personal emails for kernel work.")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Analyze corporate kernel contributions")
    parser.add_argument('--data', '-d', type=Path, required=True,
                        help='Git log output (pipe-delimited: hash|email|date|subject)')
    parser.add_argument('--output', '-o', type=Path, help='Save results CSV')
    parser.add_argument('--yearly', '-y', type=Path, help='Save yearly breakdown CSV')
    args = parser.parse_args()
    
    print("Loading git log...")
    df = load_git_log(args.data)
    print(f"Loaded {len(df):,} commits")
    
    print("Analyzing contributions...")
    results, yearly = analyze_contributions(df)
    
    print_report(results, yearly)
    
    if args.output:
        results.to_csv(args.output, index=False)
        print(f"\nSaved: {args.output}")
    
    if args.yearly:
        yearly.to_csv(args.yearly)
        print(f"Saved: {args.yearly}")


if __name__ == "__main__":
    main()
