# Setup Guide (macOS/Linux)

## Quick Start, or see Advanced (Manual Conda) below

The easiest way with conda env:
```bash
pip install -r requirements.txt
```
If 
```bash
-bash: pip: command not found
```
Then,
```bash
conda install pip
pip install -r requirements.txt
streamlit run app.py
```



If Conda is already installed and available in your terminal, just run:
```bash
./run_alert_app_conda.sh
```
- The script creates/activates the `manuscript_alert` Conda env if needed, installs dependencies only when `requirements.txt` changes, and launches Streamlit with hot reload (`--server.runOnSave true`).
- The app opens at http://localhost:8501

## Check Prerequisites

Verify Conda is installed and initialized:
```bash
conda -V && which conda
```
- If both return a value, proceed with the Quick Start above.
- If not installed, install Miniconda/Miniforge, run `conda init <your_shell>`, restart terminal, then run the launcher.

## Remote Access (optional)

- SSH port forwarding (recommended):
```bash
ssh -L 8501:localhost:8501 your_username@remote_server_ip
```
Then open http://localhost:8501.

- Expose on network (use with care):
```bash
streamlit run app.py --server.headless true --server.port 8501 --server.address 0.0.0.0 --server.runOnSave true
```

## Troubleshooting

- Port 8501 busy:
```bash
pkill -f streamlit || true
./run_alert_app_conda.sh
```
- No Conda found: install Conda, run `conda init zsh` (macOS) or `conda init bash` (Linux), restart terminal.
- Force-skip dependency check (faster startup):
```bash
FAST=1 ./run_alert_app_conda.sh
```

## Advanced (Manual Conda)

```bash
conda create -n manuscript_alert python=3.11
conda activate manuscript_alert
pip install -r requirements.txt
streamlit run app.py --server.runOnSave true
```

## Uninstall

```bash
conda deactivate || true
conda env remove -n manuscript_alert || true
```

