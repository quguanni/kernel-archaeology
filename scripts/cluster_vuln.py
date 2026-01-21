#!/usr/bin/env python3
"""
Cluster and visualize kernel vulnerabilities using dimensionality reduction.

Uses t-SNE and UMAP to project vulnerability features into 2D space,
then applies K-Means clustering to identify vulnerability patterns.

Prerequisites:
    pip install umap-learn scikit-learn matplotlib pandas numpy

Usage:
    python cluster_vuln.py --features vuln_features.npy --labels vuln_labels.csv
    python cluster_vuln.py --features vuln_features.npy --labels vuln_labels.csv --output figures/
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans

plt.style.use('seaborn-v0_8-whitegrid')

# Optional UMAP import
try:
    import umap
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False
    print("Note: UMAP not installed. Install with: pip install umap-learn")


def load_data(features_path: Path, labels_path: Path, sample_size: int = 15000):
    """Load and optionally subsample feature matrix and labels."""
    X = np.load(features_path)
    labels = pd.read_csv(labels_path)
    
    # Subsample for performance (t-SNE is O(n²))
    if len(X) > sample_size:
        idx = np.random.choice(len(X), sample_size, replace=False)
        X = X[idx]
        labels = labels.iloc[idx].reset_index(drop=True)
    
    # Scale and clean
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = np.nan_to_num(X_scaled, nan=0, posinf=0, neginf=0)
    
    return X_scaled, labels


def compute_embeddings(X: np.ndarray) -> dict:
    """Compute t-SNE and UMAP embeddings."""
    embeddings = {}
    
    print("Running t-SNE...")
    tsne = TSNE(n_components=2, perplexity=30, random_state=42, n_iter=1000)
    embeddings['tsne'] = tsne.fit_transform(X)
    
    if HAS_UMAP:
        print("Running UMAP...")
        reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
        embeddings['umap'] = reducer.fit_transform(X)
    
    return embeddings


def compute_clusters(X: np.ndarray, n_clusters: int = 8) -> np.ndarray:
    """Apply K-Means clustering."""
    print(f"Running K-Means (k={n_clusters})...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    return kmeans.fit_predict(X)


def prepare_color_mappings(labels: pd.DataFrame):
    """Prepare categorical color mappings for visualization."""
    # Subsystem colors
    subsystems = labels['subsystem'].fillna('unknown')
    top_subsystems = subsystems.value_counts().head(10).index.tolist()
    subsystem_colors = [top_subsystems.index(s) if s in top_subsystems else 10 for s in subsystems]
    
    # Bug type colors
    bug_types = labels['bug_type'].fillna('unknown')
    top_bugs = bug_types.value_counts().head(8).index.tolist()
    bugtype_colors = [top_bugs.index(b) if b in top_bugs else 8 for b in bug_types]
    
    # Lifetime colors (normalized)
    lifetimes = labels['lifetime_days'].fillna(0)
    lifetime_colors = np.clip(lifetimes / 1000, 0, 5)
    
    return {
        'subsystem': (subsystem_colors, top_subsystems),
        'bug_type': (bugtype_colors, top_bugs),
        'lifetime': lifetime_colors,
    }


def plot_embeddings(embeddings: dict, clusters: np.ndarray, color_maps: dict, 
                    output_dir: Path):
    """Generate embedding visualizations."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for method, coords in embeddings.items():
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        fig.suptitle(f'{method.upper()} Embeddings of Kernel Vulnerabilities', fontsize=14)
        
        # By subsystem
        ax = axes[0, 0]
        scatter = ax.scatter(coords[:, 0], coords[:, 1], 
                            c=color_maps['subsystem'][0], cmap='tab10', alpha=0.5, s=5)
        ax.set_title('Colored by Subsystem (top 10)')
        ax.set_xlabel(f'{method.upper()} 1')
        ax.set_ylabel(f'{method.upper()} 2')
        
        # By bug type
        ax = axes[0, 1]
        scatter = ax.scatter(coords[:, 0], coords[:, 1], 
                            c=color_maps['bug_type'][0], cmap='Set1', alpha=0.5, s=5)
        ax.set_title('Colored by Bug Type (top 8)')
        ax.set_xlabel(f'{method.upper()} 1')
        ax.set_ylabel(f'{method.upper()} 2')
        
        # By lifetime
        ax = axes[1, 0]
        scatter = ax.scatter(coords[:, 0], coords[:, 1], 
                            c=color_maps['lifetime'], cmap='RdYlGn_r', alpha=0.5, s=5)
        ax.set_title('Colored by Lifetime (red = longer)')
        ax.set_xlabel(f'{method.upper()} 1')
        ax.set_ylabel(f'{method.upper()} 2')
        plt.colorbar(scatter, ax=ax, label='Lifetime (normalized)')
        
        # By cluster
        ax = axes[1, 1]
        scatter = ax.scatter(coords[:, 0], coords[:, 1], 
                            c=clusters, cmap='tab10', alpha=0.5, s=5)
        ax.set_title('K-Means Clusters')
        ax.set_xlabel(f'{method.upper()} 1')
        ax.set_ylabel(f'{method.upper()} 2')
        
        plt.tight_layout()
        plt.savefig(output_dir / f'{method}_clusters.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_dir / f'{method}_clusters.png'}")


def plot_cluster_analysis(clusters: np.ndarray, labels: pd.DataFrame, output_dir: Path):
    """Analyze and visualize cluster characteristics."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    n_clusters = len(np.unique(clusters))
    
    # Cluster sizes
    ax = axes[0, 0]
    sizes = pd.Series(clusters).value_counts().sort_index()
    ax.bar(sizes.index, sizes.values, color='steelblue', edgecolor='white')
    ax.set_xlabel('Cluster')
    ax.set_ylabel('Size')
    ax.set_title('Cluster Size Distribution')
    
    # Lifetime by cluster
    ax = axes[0, 1]
    cluster_lifetimes = [labels.loc[clusters == c, 'lifetime_days'].mean() 
                         for c in range(n_clusters)]
    ax.bar(range(n_clusters), cluster_lifetimes, color='coral', edgecolor='white')
    ax.set_xlabel('Cluster')
    ax.set_ylabel('Mean Lifetime (days)')
    ax.set_title('Vulnerability Lifetime by Cluster')
    
    # Subsystem distribution
    ax = axes[1, 0]
    subsystems = labels['subsystem'].fillna('unknown')
    top_subs = subsystems.value_counts().head(8).index.tolist()
    crosstab = pd.crosstab(clusters, subsystems)[top_subs]
    crosstab.plot(kind='bar', stacked=True, ax=ax, colormap='tab10', legend=False)
    ax.set_xlabel('Cluster')
    ax.set_ylabel('Count')
    ax.set_title('Subsystem Distribution by Cluster')
    ax.legend(title='Subsystem', bbox_to_anchor=(1.02, 1), fontsize=8)
    
    # Bug type distribution
    ax = axes[1, 1]
    bug_types = labels['bug_type'].fillna('unknown')
    top_bugs = bug_types.value_counts().head(6).index.tolist()
    crosstab = pd.crosstab(clusters, bug_types)[top_bugs]
    crosstab.plot(kind='bar', stacked=True, ax=ax, colormap='Set2', legend=False)
    ax.set_xlabel('Cluster')
    ax.set_ylabel('Count')
    ax.set_title('Bug Type Distribution by Cluster')
    ax.legend(title='Bug Type', bbox_to_anchor=(1.02, 1), fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'cluster_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_dir / 'cluster_analysis.png'}")


def print_cluster_summary(clusters: np.ndarray, labels: pd.DataFrame):
    """Print cluster characteristics."""
    print("\n" + "=" * 60)
    print("CLUSTER SUMMARY")
    print("=" * 60)
    
    for c in range(len(np.unique(clusters))):
        mask = clusters == c
        cluster_data = labels[mask]
        
        top_subsystems = cluster_data['subsystem'].value_counts().head(3).to_dict()
        top_bugs = cluster_data['bug_type'].value_counts().head(3).to_dict()
        
        print(f"\nCluster {c} (n={mask.sum():,}):")
        print(f"  Mean lifetime: {cluster_data['lifetime_days'].mean():.0f} days")
        print(f"  Top subsystems: {top_subsystems}")
        print(f"  Top bug types: {top_bugs}")


def main():
    parser = argparse.ArgumentParser(description="Cluster kernel vulnerabilities")
    parser.add_argument('--features', '-f', type=Path, required=True,
                        help='Path to feature matrix (numpy .npy file)')
    parser.add_argument('--labels', '-l', type=Path, required=True,
                        help='Path to labels CSV')
    parser.add_argument('--output', '-o', type=Path, default=Path('.'),
                        help='Output directory for plots')
    parser.add_argument('--clusters', '-k', type=int, default=8,
                        help='Number of clusters (default: 8)')
    parser.add_argument('--sample', '-s', type=int, default=15000,
                        help='Sample size for visualization (default: 15000)')
    args = parser.parse_args()
    
    print("Loading data...")
    X, labels = load_data(args.features, args.labels, args.sample)
    print(f"Using {len(X):,} samples with {X.shape[1]} features")
    
    embeddings = compute_embeddings(X)
    clusters = compute_clusters(X, args.clusters)
    color_maps = prepare_color_mappings(labels)
    
    print("\nGenerating visualizations...")
    plot_embeddings(embeddings, clusters, color_maps, args.output)
    plot_cluster_analysis(clusters, labels, args.output)
    
    print_cluster_summary(clusters, labels)
    print("\nDone.")


if __name__ == "__main__":
    main()
