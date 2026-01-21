#!/usr/bin/env python3
"""
Visualize corporate contributions to the Linux kernel.

Generates publication-quality figures showing contribution patterns
by company, over time, and corporate vs independent development.

Usage:
    python visualize_corporate.py --results corporate_results.csv --yearly corporate_yearly.csv
    python visualize_corporate.py --results results.csv --yearly yearly.csv --output figures/
"""

import argparse
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.style.use('seaborn-v0_8-whitegrid')

# Brand colors for major companies
COMPANY_COLORS = {
    'Google': '#4285F4',
    'Intel': '#0071C5',
    'Red Hat': '#EE0000',
    'Microsoft': '#00A4EF',
    'Meta': '#0081FB',
    'Amazon': '#FF9900',
    'IBM': '#054ADA',
    'Samsung': '#1428A0',
    'Huawei': '#C7000B',
    'NVIDIA': '#76B900',
    'AMD': '#ED1C24',
    'Oracle': '#F80000',
    'Arm': '#0091BD',
    'Qualcomm': '#3253DC',
    'SUSE': '#73BA25',
    'Canonical': '#E95420',
    'Linaro': '#00BFA5',
    'Independent/Other': '#888888',
    'Unknown': '#CCCCCC',
}


def get_color(company: str) -> str:
    """Get color for company, with consistent fallback."""
    if company in COMPANY_COLORS:
        return COMPANY_COLORS[company]
    # Generate consistent color from hash
    return '#' + hex(hash(company) % 0xFFFFFF)[2:].zfill(6)


def plot_top_companies(results: pd.DataFrame, output_path: Path):
    """Horizontal bar chart of top corporate contributors."""
    known = results[~results['company'].isin(['Independent/Other', 'Unknown'])]
    known = known.sort_values('commits', ascending=True).tail(15)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = [get_color(c) for c in known['company']]
    bars = ax.barh(known['company'], known['commits'], color=colors, edgecolor='white')
    
    for bar, pct in zip(bars, known['percentage']):
        ax.text(bar.get_width() + 1000, bar.get_y() + bar.get_height()/2,
                f'{bar.get_width():,.0f} ({pct:.1f}%)', va='center', fontsize=9)
    
    ax.set_xlabel('Number of Commits', fontsize=12)
    ax.set_title('Top 15 Corporate Contributors to Linux Kernel (2005-2025)', fontsize=14)
    ax.set_xlim(0, known['commits'].max() * 1.15)
    ax.xaxis.grid(True, linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='white', bbox_inches='tight')
    plt.close()


def plot_contribution_share(results: pd.DataFrame, output_path: Path):
    """Donut chart showing contribution breakdown."""
    known = results[~results['company'].isin(['Independent/Other', 'Unknown'])]
    top10 = known.nlargest(10, 'commits')
    other_corp = known[~known['company'].isin(top10['company'])]['commits'].sum()
    independent = results.loc[results['company'] == 'Independent/Other', 'commits'].sum()
    
    labels = list(top10['company']) + ['Other Corporate', 'Independent']
    sizes = list(top10['commits']) + [other_corp, independent]
    colors = [get_color(c) for c in top10['company']] + ['#666666', '#888888']
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    wedges, _, autotexts = ax.pie(
        sizes, labels=None,
        autopct=lambda p: f'{p:.1f}%' if p > 2 else '',
        colors=colors, pctdistance=0.75, startangle=90,
        wedgeprops=dict(width=0.6, edgecolor='white')
    )
    
    legend_labels = [f'{l}: {s:,}' for l, s in zip(labels, sizes)]
    ax.legend(wedges, legend_labels, loc='center left', bbox_to_anchor=(1, 0.5),
              fontsize=9, title='Contributors')
    ax.set_title('Linux Kernel Contributions by Organization', fontsize=14)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='white', bbox_inches='tight')
    plt.close()


def plot_yearly_stacked(yearly: pd.DataFrame, output_path: Path):
    """Stacked area chart of contributions over time."""
    totals = yearly.sum().sort_values(ascending=False)
    top10 = [c for c in totals.index if c not in ['Independent/Other', 'Unknown']][:10]
    
    df = yearly[top10].copy()
    df['Other'] = yearly.drop(columns=top10, errors='ignore').sum(axis=1)
    df = df[(df.index >= 2005) & (df.index <= 2025)]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    colors = [get_color(c) for c in top10] + ['#888888']
    ax.stackplot(df.index, df.T, labels=list(df.columns), colors=colors, alpha=0.8)
    
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Number of Commits', fontsize=12)
    ax.set_title('Linux Kernel Contributions Over Time', fontsize=14)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=9)
    ax.set_xlim(df.index.min(), df.index.max())
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='white', bbox_inches='tight')
    plt.close()


def plot_market_share(yearly: pd.DataFrame, output_path: Path):
    """Line chart of company market share over time."""
    totals = yearly.sum().sort_values(ascending=False)
    top8 = [c for c in totals.index if c not in ['Independent/Other', 'Unknown']][:8]
    
    yearly_pct = yearly.div(yearly.sum(axis=1), axis=0) * 100
    df = yearly_pct[top8]
    df = df[(df.index >= 2005) & (df.index <= 2025)]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for company in top8:
        ax.plot(df.index, df[company], marker='o', markersize=4,
                linewidth=2, label=company, color=get_color(company))
    
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Percentage of Total Commits', fontsize=12)
    ax.set_title('Corporate Market Share of Linux Kernel Development', fontsize=14)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
    ax.grid(True, linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='white', bbox_inches='tight')
    plt.close()


def plot_corporate_vs_independent(yearly: pd.DataFrame, output_path: Path):
    """Compare corporate vs independent contributions."""
    totals = yearly.sum().sort_values(ascending=False)
    corporate_cols = [c for c in totals.index if c not in ['Independent/Other', 'Unknown']]
    
    df = pd.DataFrame({
        'Corporate': yearly[corporate_cols].sum(axis=1),
        'Independent': yearly.get('Independent/Other', 0),
    })
    df = df[(df.index >= 2005) & (df.index <= 2025)]
    df_pct = df.div(df.sum(axis=1), axis=0) * 100
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Absolute
    ax1.stackplot(df.index, df['Corporate'], df['Independent'],
                  labels=['Corporate', 'Independent'], colors=['#2E86AB', '#888888'], alpha=0.8)
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Commits')
    ax1.set_title('Total Commits')
    ax1.legend(loc='upper left')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))
    
    # Percentage
    ax2.stackplot(df_pct.index, df_pct['Corporate'], df_pct['Independent'],
                  labels=['Corporate', 'Independent'], colors=['#2E86AB', '#888888'], alpha=0.8)
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Percentage')
    ax2.set_title('Percentage Share')
    ax2.legend(loc='upper left')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
    ax2.set_ylim(0, 100)
    
    fig.suptitle('Corporate vs Independent Linux Kernel Development', fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='white', bbox_inches='tight')
    plt.close()


def plot_dashboard(results: pd.DataFrame, yearly: pd.DataFrame, output_path: Path):
    """Summary dashboard with key visualizations."""
    fig = plt.figure(figsize=(16, 12))
    
    known = results[~results['company'].isin(['Independent/Other', 'Unknown'])]
    known = known.sort_values('commits', ascending=True).tail(10)
    
    # Top 10 bar chart
    ax1 = fig.add_subplot(2, 2, 1)
    colors = [get_color(c) for c in known['company']]
    ax1.barh(known['company'], known['commits'], color=colors, edgecolor='white')
    ax1.set_xlabel('Commits')
    ax1.set_title('Top 10 Contributors', fontweight='bold')
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))
    
    # Pie chart
    ax2 = fig.add_subplot(2, 2, 2)
    top5 = known.nlargest(5, 'commits')
    other = known[~known['company'].isin(top5['company'])]['commits'].sum()
    independent = results.loc[results['company'] == 'Independent/Other', 'commits'].sum()
    
    pie_labels = list(top5['company']) + ['Other Corp', 'Independent']
    pie_sizes = list(top5['commits']) + [other, independent]
    pie_colors = [get_color(c) for c in top5['company']] + ['#666', '#888']
    
    ax2.pie(pie_sizes, autopct=lambda p: f'{p:.1f}%' if p > 3 else '',
            colors=pie_colors, pctdistance=0.75, wedgeprops=dict(width=0.5, edgecolor='white'))
    ax2.legend(pie_labels, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)
    ax2.set_title('Contribution Share', fontweight='bold')
    
    # Timeline
    ax3 = fig.add_subplot(2, 2, 3)
    totals = yearly.sum().sort_values(ascending=False)
    top6 = [c for c in totals.index if c not in ['Independent/Other', 'Unknown']][:6]
    yearly_pct = yearly.div(yearly.sum(axis=1), axis=0) * 100
    df_timeline = yearly_pct[top6]
    df_timeline = df_timeline[(df_timeline.index >= 2010) & (df_timeline.index <= 2025)]
    
    for company in top6:
        ax3.plot(df_timeline.index, df_timeline[company], marker='o', markersize=3,
                 linewidth=2, label=company, color=get_color(company))
    ax3.set_xlabel('Year')
    ax3.set_ylabel('% of Commits')
    ax3.set_title('Market Share (2010-2025)', fontweight='bold')
    ax3.legend(fontsize=7, ncol=2)
    ax3.grid(True, linestyle='--', alpha=0.3)
    
    # Corporate vs Independent
    ax4 = fig.add_subplot(2, 2, 4)
    corp_cols = [c for c in totals.index if c not in ['Independent/Other', 'Unknown']]
    corp_total = yearly[corp_cols].sum(axis=1)
    indep_total = yearly.get('Independent/Other', pd.Series(0, index=yearly.index))
    total_per_year = yearly.sum(axis=1)
    
    years = [y for y in corp_total.index if 2010 <= y <= 2025]
    corp_pct = [(corp_total[y] / total_per_year[y] * 100) for y in years]
    
    ax4.fill_between(years, corp_pct, alpha=0.7, label='Corporate', color='#2E86AB')
    ax4.set_xlabel('Year')
    ax4.set_ylabel('% Corporate')
    ax4.set_title('Corporate Development Share', fontweight='bold')
    ax4.set_ylim(0, 100)
    
    fig.suptitle('Linux Kernel Corporate Contributions (2005-2025)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='white', bbox_inches='tight')
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Visualize corporate kernel contributions")
    parser.add_argument('--results', '-r', type=Path, required=True,
                        help='Corporate results CSV')
    parser.add_argument('--yearly', '-y', type=Path, required=True,
                        help='Yearly breakdown CSV')
    parser.add_argument('--output', '-o', type=Path, default=Path('.'),
                        help='Output directory')
    args = parser.parse_args()
    
    print("Loading data...")
    results = pd.read_csv(args.results)
    yearly = pd.read_csv(args.yearly, index_col=0)
    
    args.output.mkdir(parents=True, exist_ok=True)
    
    print("Generating visualizations...")
    plot_top_companies(results, args.output / 'corporate_top_companies.png')
    plot_contribution_share(results, args.output / 'corporate_pie_chart.png')
    plot_yearly_stacked(yearly, args.output / 'corporate_yearly_stacked.png')
    plot_market_share(yearly, args.output / 'corporate_market_share.png')
    plot_corporate_vs_independent(yearly, args.output / 'corporate_vs_independent.png')
    plot_dashboard(results, yearly, args.output / 'corporate_dashboard.png')
    
    print(f"Saved 6 figures to {args.output}/")


if __name__ == "__main__":
    main()
