# Data

This directory is intentionally empty. Data is loaded directly from HuggingFace:
```python
from datasets import load_dataset
ds = load_dataset("pebblebed/kernel-vuln-dataset")
```

If you need local copies for offline analysis, the scripts will cache them here.
