# Installing Manuscript Alert System on a New Computer

This guide will help you install the Manuscript Alert System on a different computer using conda.

## Prerequisites

### 1. Install Conda (if not already installed)
```bash
# Download Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Install Miniconda
bash Miniconda3-latest-Linux-x86_64.sh

# Restart your terminal or run:
source ~/.bashrc
```

### 2. System Requirements
- Linux operating system
- Python 3.7 or higher
- Internet connection
- Web browser

## Installation Steps

### Step 1: Transfer Your Project Files
Copy your project folder to the new computer. You can use:
- USB drive
- Cloud storage (Google Drive, Dropbox, etc.)
- Git repository
- SCP/SFTP for remote transfer

### Step 2: Create a Conda Environment
```bash
# Create a new conda environment
conda create -n manuscript_alert python=3.11

# Activate the environment
conda activate manuscript_alert
```

### Step 3: Install the App
```bash
# Navigate to your project directory
cd /path/to/your/manuscript-alert-system

# Make the installer executable
chmod +x install_on_new_computer.sh

# Run the installer
./install_on_new_computer.sh
```

## Alternative: Manual Installation

If you prefer to install manually:

### 1. Activate Your Conda Environment
```bash
conda activate your_environment_name
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Make Launcher Executable
```bash
chmod +x run_alert_app_conda.sh
```

### 4. Create Desktop Entry (Optional)
```bash
# Copy the desktop file
cp ManuscriptAlert.desktop ~/.local/share/applications/

# Update the Exec path in the desktop file to point to your installation
sed -i "s|Exec=.*|Exec=$(pwd)/run_alert_app_conda.sh|" ~/.local/share/applications/ManuscriptAlert.desktop
```

## Launching the App

### Method 1: Application Menu
- Search for "Manuscript Alert System" in your application menu
- Click to launch

### Method 2: Command Line
```bash
conda activate your_environment_name
./run_alert_app_conda.sh
```

### Method 3: Direct Streamlit
```bash
conda activate your_environment_name
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
chmod +x install_on_new_computer.sh
chmod +x run_alert_app_conda.sh
```

**"Module not found"**
```bash
conda activate your_environment_name
pip install -r requirements.txt
```

**"Port 8501 already in use"**
```bash
# Kill existing process
pkill -f streamlit
# Or use a different port
streamlit run app.py --server.port 8502
```

### Environment-Specific Issues

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**CentOS/RHEL:**
```bash
sudo yum install python3 python3-pip
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip
```

## File Structure on New Computer

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
├── run_alert_app_conda.sh         # Conda launcher script
├── install_on_new_computer.sh     # New computer installer
├── ManuscriptAlert.desktop         # Desktop entry
├── README.md                       # Documentation
└── INSTALL_NEW_COMPUTER.md        # This file
```

## Uninstallation

To remove the app from the new computer:

1. **Delete the project folder**
2. **Remove the desktop entry:**
   ```bash
   rm ~/.local/share/applications/manuscript-alert.desktop
   ```
3. **Remove the icon (optional):**
   ```bash
   rm ~/.local/share/icons/manuscript-alert.svg
   ```
4. **Remove the conda environment (optional):**
   ```bash
   conda deactivate
   conda env remove -n manuscript_alert
   ```

## Quick Start Checklist

- [ ] Install conda
- [ ] Create conda environment
- [ ] Transfer project files
- [ ] Run installer script
- [ ] Test the app
- [ ] Configure keywords
- [ ] Search for papers

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Ensure your conda environment is activated
3. Verify all dependencies are installed
4. Check the terminal output for error messages

---

**Note**: The app requires an internet connection to fetch papers from various APIs. Make sure your new computer has internet access. 