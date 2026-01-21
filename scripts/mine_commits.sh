#!/bin/bash
#
# Extract commit metadata from a Linux kernel git repository.
#
# Usage:
#   ./mine_commits.sh /path/to/linux > commits.csv
#   ./mine_commits.sh                              # Uses current directory
#
# Output format (pipe-delimited):
#   commit_hash|author_email|author_date|subject
#
# This data is used by:
#   - corporate_contributions.py (analyze company contributions)
#   - analyze_vuln_rate.py (compute vulnerability rates)

set -e

KERNEL_PATH="${1:-.}"

if [ ! -d "$KERNEL_PATH/.git" ]; then
    echo "Error: $KERNEL_PATH is not a git repository" >&2
    echo "Usage: $0 /path/to/linux" >&2
    exit 1
fi

echo "Extracting commits from $KERNEL_PATH..." >&2
echo "This may take a few minutes..." >&2

cd "$KERNEL_PATH"

# Extract commits in pipe-delimited format
# %H  = commit hash
# %ae = author email
# %ai = author date (ISO 8601)
# %s  = subject line
git log --format="%H|%ae|%ai|%s" --since="2005-01-01" --all

echo "Done." >&2
