# MNE Analyze Python (STC Viewer)

High-performance 3D brain viewer for MNE source estimation data.

## Quick Start

### 1. Install uv
Use pip to install `uv` (a fast Python package installer and unifier).

```bash
pip install uv
```
> **Note:** If your system uses `python3` command, you may need to use `pip3 install uv`.

### 2. Run
This single command automatically creates a virtual environment, installs all required packages from `pyproject.toml`, and starts the application:

```bash
uv run python main.py
```

---

### Troubleshooting

#### SSL / Certificate Errors
If you encounter an `invalid peer certificate` error (common on corporate networks), run:

```bash
uv run --native-tls python main.py
```
