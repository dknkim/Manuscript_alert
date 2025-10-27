# Manuscript Alert System for AD and Neuroimaging

A local web application that helps researchers stay updated with the latest papers in Alzheimer's disease and neuroimaging from PubMed, arXiv, bioRxiv, and medRxiv.

---
## ⚡ I've only tested Mac and Linux systems with Conda ⚡

**📱 Setup Guide:** See [docs/setup_guide.md](docs/setup_guide.md) for detailed setup and troubleshooting.
## 🐍 Run (Conda, Recommended)

Just run (linux):
```bash
./run_alert_app_conda.sh
```

Just run (Mac):
```bash
streamlit run app.py 
   
```
- The script creates/activates the `manuscript_alert` Conda env if needed, installs dependencies only when `requirements.txt` changes, and launches the app with hot reload.
- The app opens at http://localhost:8501

#### ⚡ Running Remotely ⚡ ###
If you are running the app on a remote server (e.g., via SSH), you will not be able to access http://localhost:8501 directly from your local browser. Use one of the following methods:

**Option 1: SSH Port Forwarding (Recommended)**
1. On your local machine, run:
   ```bash
   ssh -L 8501:localhost:8501 your_username@remote_server_ip
   ```
2. Then open [http://localhost:8501](http://localhost:8501) in your local browser.

**Option 2: Access via Network/External URL**
1. Launch the app with this command (or modify the script):
   For local run,
  
   ```bash

   streamlit run app.py --server.headless true --server.port 8501 --server.address 0.0.0.0 --server.runOnSave true
   ```
2. Open the Network or External URL shown in the terminal (e.g., http://10.110.5.6:8501 or http://171.66.11.71:8501) from your local browser.
3. Make sure your server's firewall allows inbound connections on port 8501:
   ```bash
   sudo ufw allow 8501
   ```

> **Note:** Exposing the app to the internet can have security implications. SSH port forwarding is safer for most users.

### 4. Stopping and Restarting the App
- To stop: Press `Ctrl+C` in the terminal where the app is running.
- To restart after making changes to `app.py`:
  ```bash
  ./run_alert_app_conda.sh
  ```

### 5. If You See "Port 8501 is already in use", Or Choose different port
- Find the process using the port:
  ```bash
  netstat -tlnp | grep 8501
  # Example output: tcp 0 0 0.0.0.0:8501 0.0.0.0:* LISTEN 12345/python3.11
  ```
- Kill the process (replace 12345 with your PID):
  ```bash
  kill -9 12345
  # If needed, use sudo: sudo kill -9 12345
  ```
- Then restart the app.

### 6. Example Workflow (Full Session)
```bash
# 1. Start the app (first run bootstraps env and installs deps)
./run_alert_app_conda.sh

# 2. After code changes, stop (Ctrl+C) and re-run
./run_alert_app_conda.sh

# 3. If you get a port error, find and kill the process:
netstat -tlnp | grep 8501
kill -9 <PID>
./run_alert_app_conda.sh
```
---

## Features

- **Multi-source paper fetching**: PubMed, arXiv, bioRxiv, and medRxiv
- **Smart keyword matching**: Papers must match at least 2 keywords to be displayed
- **Relevance scoring**: Papers are ranked by relevance to your research interests
- **Journal quality filtering**: Option to show only papers from high-impact journals
- **Configurable search parameters**: Date range, search limits, and data sources
- **Export functionality**: Download results as CSV
- **Real-time statistics**: Source distribution and keyword analysis

## System Requirements

- Linux operating system
- Python 3.7 or higher
- Internet connection for fetching papers

## Installation using venv (legacy, not recommended)

### Quick Install⚡

1. **Download or clone the project** to your local machine
2. **Make the installer executable**:
   ```bash
   chmod +x install.sh
   ```
3. **Run the installer**:
   ```bash
   ./install.sh
   ```

The installer will:
- Check for Python 3 and pip
- Create a virtual environment
- Install all dependencies
- Create a desktop entry for easy launching
- Set up a custom icon

### Manual Installation

If you prefer to install manually:

1. **Install Python dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Launch via the legacy script:
   ```bash
   scripts/legacy/run_alert_app.sh
   ```

3. **Create a desktop entry** (optional):
   ```bash
   cp ManuscriptAlert.desktop ~/.local/share/applications/
   ```
   *Note: Update the Exec path in the .desktop file to point to your installation directory*

## Usage

### Launching the App

**Option 1: Application Menu**
- Search for "Manuscript Alert System" in your application menu
- Click to launch

**Option 2: Command Line (legacy venv path)**
```bash
scripts/legacy/run_alert_app.sh
```

**Option 3: Direct Streamlit Command**
```bash
source venv/bin/activate
streamlit run app.py
```

### Using the App

1. **Configure Keywords**: Add research topics you're interested in (one per line)
2. **Set Date Range**: Choose how many days back to search
3. **Select Data Sources**: Choose which databases to search (PubMed, arXiv, etc.)
4. **Adjust Search Limits**: Choose between Brief, Standard, or Extended search modes
5. **Apply Filters**: Use the search box to filter results, or enable journal quality filtering
6. **View Results**: Papers are ranked by relevance score and displayed with abstracts

### Default Keywords

The app comes with these default keywords:
- Alzheimer's disease
- PET
- MRI
- dementia
- amyloid
- tau
- plasma
- brain

## Configuration

### Keywords
- Add your research interests in the sidebar
- Papers must match at least 2 keywords to be displayed
- Keywords are saved automatically

### Date Range
- Choose from 1-21 days back from today
- Longer ranges may take more time to search

### Search Modes
- **Brief**: Fastest, PubMed: 1000, Others: 500 papers
- **Standard**: Balanced, PubMed: 2500, Others: 1000 papers  
- **Extended**: Comprehensive, All sources: 5000 papers

### Journal Quality Filter
When enabled, shows only papers from:
- Nature/JAMA/NPJ/Science journals
- Radiology, AJNR, Brain
- MRM, JMRI
- Alzheimer's & Dementia

## Troubleshooting

### Common Issues

**"Python 3 is not installed"**
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip

# Arch
sudo pacman -S python python-pip
```

**"Permission denied"**
```bash
chmod +x run_alert_app.sh
chmod +x install.sh
```

**"Module not found"**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**App doesn't open in browser**
- Check if port 8501 is available
- Try accessing http://localhost:8501 manually
- Check firewall settings

### Logs and Debugging

The app runs in the terminal, so you can see any error messages directly. Common debug steps:

1. **Check if Streamlit is running**:
   ```bash
   ps aux | grep streamlit
   ```

2. **Check port usage**:
   ```bash
   netstat -tlnp | grep 8501
   ```

3. **Clear cache**:
   ```bash
   rm -rf ~/.streamlit/
   ```

## Uninstallation

To remove the app:

1. **Delete the project folder**
2. **Remove the desktop entry**:
   ```bash
   rm ~/.local/share/applications/manuscript-alert.desktop
   ```
3. **Remove the icon** (optional):
   ```bash
   rm ~/.local/share/icons/manuscript-alert.svg
   ```

## Technical Details

### Architecture
- **Frontend**: Streamlit web interface
- **Backend**: Python with concurrent API fetching
- **Data Sources**: PubMed, arXiv, bioRxiv APIs
- **Storage**: Local file-based caching and preferences

### Dependencies
- `streamlit`: Web framework
- `pandas`: Data manipulation
- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `lxml`: XML parsing
- `feedparser`: RSS feed parsing

### File Structure
```
manuscript-alert-system/
├── app.py                 # Main application
├── arxiv_fetcher.py      # arXiv API integration
├── biorxiv_fetcher.py    # bioRxiv/medRxiv integration
├── pubmed_fetcher.py     # PubMed API integration
├── keyword_matcher.py    # Keyword matching logic
├── data_storage.py       # Local data persistence
├── requirements.txt      # Python dependencies
├── run_alert_app.sh     # Launcher script
├── install.sh           # Installation script
├── ManuscriptAlert.desktop # Desktop entry
└── README.md            # This file
```


## License

This project is open source, but not for commercial use. Buy me a coffee when we meet.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs in the terminal
3. Create an issue in the project repository

---

**Note**: This app requires an internet connection to fetch papers from the various APIs. The app will cache results locally to improve performance on subsequent runs. 

---

## 📚 Documentation

### Setup & Configuration
- **[Setup Guide](docs/setup/SETUP_GUIDE.md)** - Quick setup for new installations
- **[User Guide](docs/USER_GUIDE.md)** - Complete user documentation
- **[Settings Guide](docs/SETTINGS_GUIDE.md)** - Configure keywords, journals, scoring

### Admin Tools
- **[Admin Tools](utils/admin_tools/README.md)** - Manage users and admins
- **Promote to Admin**: `python utils/admin_tools/promote_to_admin.py`
- **List Users**: `python utils/admin_tools/list_users.py`

### Technical Documentation
- **[Supabase Integration PRD](docs/PRD_Supabase_Integration.md)** - Database & auth architecture
- **[UX Improvements](docs/ux_improvements.md)** - UI/UX enhancement plans

---

## 🗄️ Database

This app uses **Supabase** (PostgreSQL) for:
- User authentication (email-based)
- Role-based access control (admin/user/guest)
- Cloud data storage
- Multi-user support

**Database Schema**: See [docs/setup/DROP_AND_RECREATE_EMAIL_AUTH.sql](docs/setup/DROP_AND_RECREATE_EMAIL_AUTH.sql)

---

## 👥 Multi-User Setup

**Adding Users:**
1. Users can self-register via the app
2. Or admin creates them: `python utils/admin_tools/create_admin_email.py`

**Making Someone Admin:**
```bash
python utils/admin_tools/promote_to_admin.py
```

See [User Guide](docs/USER_GUIDE.md) for details.

