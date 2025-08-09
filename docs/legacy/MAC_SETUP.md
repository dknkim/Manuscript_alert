# Setting Up Manuscript Alert System on macOS

This guide will help you install and run the Manuscript Alert System on your Mac computer.

> If Conda is already installed and available in your terminal, you can skip directly to Run the App and just run `./run_alert_app_conda.sh`.

## Prerequisites

### 1. Install Conda (if not already installed)

To check if Conda is already installed:
```bash
conda -V && which conda
```
If this prints a version and a path, Conda is installed — skip to Step 4 and run the script.

**For Apple Silicon Macs (M1/M2/M3):**
```bash
# Download Miniconda for Apple Silicon (ARM64)
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh

# Install Miniconda
bash Miniconda3-latest-MacOSX-arm64.sh

# Restart your terminal or run:
source ~/.zshrc  # or source ~/.bash_profile if using bash 
# or try 'echo $SHELL' if unsure
```

**For Intel Macs (x86_64):**
```bash
# Download Miniconda for Intel Macs
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh

# Install Miniconda
bash Miniconda3-latest-MacOSX-x86_64.sh

# Restart your terminal or run:
source ~/.zshrc  # or source ~/.bash_profile if using bash 
# or try 'echo $SHELL' if unsure
```

**To check your Mac's architecture:**
```bash
uname -m
# If it shows "arm64" → Use Apple Silicon version
# If it shows "x86_64" → Use Intel version
```

### 2. System Requirements
- macOS 10.13 or higher
- Python 3.7 or higher
- Internet connection
- Web browser (Safari, Chrome, Firefox, etc.)

### Mac Architecture Types

**Apple Silicon Macs (M1/M2/M3):**
- Use ARM64 architecture
- Generally faster performance
- More energy efficient
- Use `Miniconda3-latest-MacOSX-arm64.sh`

**Intel Macs:**
- Use x86_64 architecture
- Older Mac models (pre-2020)
- Use `Miniconda3-latest-MacOSX-x86_64.sh`

## Quick Setup (Recommended)

### Step 1: Transfer Your Project
Copy your project folder to your Mac using:
- USB drive
- Cloud storage (Google Drive, Dropbox, etc.)
- Git repository
- AirDrop

### Step 2: Check Your Mac's Architecture
First, determine if you have an Apple Silicon or Intel Mac:
```bash
uname -m
```
- If it shows `arm64` → You have an **Apple Silicon Mac** (M1/M2/M3)
- If it shows `x86_64` → You have an **Intel Mac**

### Step 3: Install Conda (if not already installed)

If `conda -V` prints a version, skip to Step 4 and run the launcher script.

**For Apple Silicon Macs (M1/M2/M3):**
```bash
# Download Miniconda for Apple Silicon (ARM64)
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh

# Install Miniconda
bash Miniconda3-latest-MacOSX-arm64.sh

# Restart your terminal or run:
source ~/.zshrc  # or source ~/.bash_profile if using bash
```

**For Intel Macs:**
```bash
# Download Miniconda for Intel Macs (x86_64)
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh

# Install Miniconda
bash Miniconda3-latest-MacOSX-x86_64.sh

# Restart your terminal or run:
source ~/.zshrc  # or source ~/.bash_profile if using bash
```

### Step 4: Run the App (single step)
```bash
# Navigate to your project directory
cd /path/to/your/manuscript-alert-system

# Run the launcher (first run bootstraps the Conda env and installs deps if needed)
./run_alert_app_conda.sh
```

## Advanced: Manual Setup (Optional)

If you prefer a simpler setup without the application bundle:

### 1. Activate Your Conda Environment
```bash
conda activate manuscript_alert
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run directly (skip the launcher)
```bash
streamlit run app.py
```

## Launching the App

### Method 1: Command Line (Recommended)
```bash
./run_alert_app_conda.sh
```

### Method 2: Direct Streamlit
```bash
conda activate manuscript_alert
streamlit run app.py
```

## Troubleshooting

### Common Issues

**"conda command not found"**
```bash
# Add conda to PATH
export PATH="$HOME/miniconda3/bin:$PATH"
# Or restart your terminal
```

**"Permission denied"**
```bash
chmod +x run_alert_app_conda.sh
```

**"Module not found"**
```bash
conda activate manuscript_alert
pip install -r requirements.txt
```

**"Port 8501 already in use"**
```bash
# Kill existing process
pkill -f streamlit
# Or use a different port
streamlit run app.py --server.port 8502
```

**"zsh: command not found: conda"**
```bash
# Initialize conda for zsh
conda init zsh
# Restart terminal or run:
source ~/.zshrc
```

**"WARNING: Your operating system appears not to be x86_64"**
```bash
# This means you're on Apple Silicon (M1/M2/M3) but downloaded Intel version
# Download the correct version for Apple Silicon:
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh
```

**"WARNING: Your operating system appears not to be arm64"**
```bash
# This means you're on Intel Mac but downloaded Apple Silicon version
# Download the correct version for Intel:
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh
```

### macOS-Specific Issues

**Gatekeeper blocking the app**
```bash
# If macOS blocks the app, go to:
# System Preferences > Security & Privacy > General
# Click "Allow Anyway" for the Manuscript Alert System
```

**Python version issues**
```bash
# Check Python version
python --version
# Should be 3.7 or higher
```

## File Structure on Mac

After installation, your directory should look like this:
```
manuscript-alert-system/
├── app.py                           # Main application
├── arxiv_fetcher.py                # arXiv API integration
├── biorxiv_fetcher.py              # bioRxiv/medRxiv integration
├── pubmed_fetcher.py               # PubMed API integration
├── keyword_matcher.py              # Keyword matching logic
├── data_storage.py                 # Local data persistence
├── requirements.txt                # Python dependencies
├── run_alert_app_conda.sh         # Single entry-point launcher (Conda)
├── MAC_SETUP.md                   # This file
└── README.md                      # Documentation
```

## Uninstallation

To remove the app from your Mac:

1. **Delete the project folder**
2. **Remove the application bundle (if created):**
   ```bash
   rm -rf ~/Applications/Manuscript\ Alert\ System.app
   ```
3. **Remove the conda environment (optional):**
   ```bash
   conda deactivate
   conda env remove -n manuscript_alert
   ```

## Quick Start Checklist

- [ ] Install Conda (if not already present)
- [ ] Transfer project files
- [ ] Run the launcher script (`./run_alert_app_conda.sh`)
- [ ] Test the app
- [ ] Configure keywords
- [ ] Search for papers

## Performance Tips for Mac

1. **Use Safari**: Generally faster for Streamlit apps on macOS
2. **Close other apps**: Free up memory for better performance
3. **Use SSD**: If possible, store the project on an SSD for faster file access
4. **Monitor Activity Monitor**: Check if the app is using too much CPU/memory

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Ensure your conda environment is activated
3. Verify all dependencies are installed
4. Check the terminal output for error messages
5. Try running with `--server.port 8502` if port 8501 is busy

---

**Note**: The app requires an internet connection to fetch papers from various APIs. Make sure your Mac has internet access. 