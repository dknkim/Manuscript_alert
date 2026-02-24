# Manuscript Alert System for AD and Neuroimaging

A local web application that helps researchers stay updated with the latest papers in Alzheimer's disease and neuroimaging from PubMed, arXiv, bioRxiv, and medRxiv.

---
## ⚡ I've only tested Mac and Linux systems with Conda ⚡

## 🚀 Quick Start (Single Command)

```bash
#conda activate your_env #if desired
python server.py
```

That's it! The server will:
1. Automatically install frontend dependencies (if needed)
2. Build the React frontend (if needed)
3. Start the application at **http://localhost:8000**

Papers from all sources (arXiv, bioRxiv, medRxiv, PubMed) are fetched automatically on startup.

### Initial Conda environment setup (first time only)

If you haven't created the `your_env` environment yet, run these commands **once**:

```bash
conda create -n your_env python=3.11 nodejs -y
conda activate your_env
pip install -r requirements.txt
python server.py
```

On subsequent runs you only need:

```bash
conda activate your_env
python server.py
```

### Development Mode

If you're working on the frontend separately with the Next.js dev server:

```bash
# Terminal 1: Start the API server (skip frontend build)
python server.py --dev

# Terminal 2: Start Next.js dev server with hot reload
cd frontend && npm run dev
```

---

## ⚡ Running Remotely

If you are running the app on a remote server (e.g., via SSH), you will not be able to access http://localhost:8000 directly from your local browser. Use one of the following methods:

**Option 1: SSH Port Forwarding (Recommended)**
1. On your local machine, run:
   ```bash
   ssh -L 8000:localhost:8000 your_username@remote_server_ip
   ```
2. Then open [http://localhost:8000](http://localhost:8000) in your local browser.

**Option 2: Access via Network/External URL**
1. The server already binds to `0.0.0.0`, so it is accessible on all network interfaces.
2. Open `http://<server_ip>:8000` from your local browser.
3. Make sure your server's firewall allows inbound connections on port 8000:
   ```bash
   sudo ufw allow 8000
   ```

> **Note:** Exposing the app to the internet can have security implications. SSH port forwarding is safer for most users.

### Stopping and Restarting
- To stop: Press `Ctrl+C` in the terminal where the server is running.
- To restart:
  ```bash
  python server.py
  ```
  The frontend is only rebuilt when source files have changed.

### If Port 8000 is Already in Use
```bash
# Find the process
lsof -i :8000
# Kill it (replace <PID> with the actual PID)
kill -9 <PID>
# Restart
python server.py
```

---

## Features

- **Multi-source paper fetching**: PubMed, arXiv, bioRxiv, and medRxiv
- **Auto-fetch on startup**: Papers are fetched automatically when the app loads
- **Smart keyword matching**: Papers must match at least 2 keywords to be displayed
- **Relevance scoring**: Papers are ranked by relevance to your research interests
- **Journal quality filtering**: Option to show only papers from high-impact journals
- **Configurable search parameters**: Date range, search limits, and data sources
- **Model presets**: Save and load different keyword/settings configurations
- **Settings backup & restore**: Automatic and manual backup of settings
- **Export functionality**: Download results as CSV
- **Real-time statistics**: Source distribution and keyword analysis
- **Persistent results**: Fetched papers persist across tab switches

## System Requirements

- macOS or Linux
- Python 3.10+
- Node.js 18+ (with npm)
- Conda (recommended) or venv
- Internet connection for fetching papers

## Installation

### Prerequisites

1. **Conda environment** (recommended):
   ```bash
   conda create -n basic python=3.11 nodejs -y
   conda activate basic
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

Frontend dependencies (npm) are installed automatically when you run `python server.py`.

---

## Usage

### Using the App

1. **Papers Tab**: Papers are fetched automatically on load. Use the sidebar to:
   - Toggle data sources (arXiv, bioRxiv, medRxiv, PubMed)
   - Select search mode (Brief / Standard / Extended)
   - Filter by journal quality
   - Search within results
   - Export to CSV
2. **Models Tab**: Save/load keyword & settings presets for different research topics
3. **Settings Tab**: Configure keywords, journal preferences, scoring parameters, and manage backups

### Default Keywords

The app comes with default keywords including:
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
- Add your research interests in the Settings tab
- Papers must match at least 2 keywords to be displayed
- Keywords are saved automatically

### Date Range
- Configurable in the Settings tab (default: 7 days back)
- Longer ranges may take more time to search

### Search Modes
- **Brief**: Fastest — PubMed: 1000, Others: 500 papers
- **Standard**: Balanced — PubMed: 2500, Others: 1000 papers
- **Extended**: Comprehensive — All sources: 5000 papers

### Journal Quality Filter
When enabled, shows only papers from relevant journals (e.g., Nature, JAMA, Science, Radiology, Brain, Alzheimer's & Dementia, etc.).

---

## Technical Details

### Architecture
- **Frontend**: Next.js 15 + React 19 + TypeScript 5.7 + Tailwind CSS 3.4
- **Backend**: FastAPI (Python 3.10+) with type hints, Pydantic models, REST API
- **Data Sources**: PubMed, arXiv, bioRxiv/medRxiv APIs
- **Storage**: Local file-based settings and model presets (JSON + Python)
- **Serving**: FastAPI serves the Next.js static export (`frontend/out/`) + REST API

### Dependencies

**Python** (`requirements.txt`):
- `fastapi` — Web framework / API server
- `uvicorn` — ASGI server
- `pandas` — Data manipulation / CSV export
- `requests` — HTTP requests
- `beautifulsoup4` — HTML parsing
- `lxml` — XML parsing
- `feedparser` — RSS feed parsing
- `ruff` — Python linter

**Frontend** (`frontend/package.json`):
- `next` — React framework (static export)
- `react` / `react-dom` — UI library
- `typescript` — Type-safe JavaScript
- `tailwindcss` — Utility-first CSS

### File Structure
```
Manuscript_alert/
├── server.py                      # FastAPI backend + static file serving
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Ruff configuration
├── config/
│   ├── settings.py                # Current application settings
│   ├── models/                    # Saved model presets (JSON)
│   └── backups/                   # Settings backups
├── core/
│   ├── paper_manager.py           # Core paper management logic
│   └── filters.py                 # Paper filtering
├── fetchers/
│   ├── arxiv_fetcher.py           # arXiv API integration
│   ├── biorxiv_fetcher.py         # bioRxiv/medRxiv API integration
│   └── pubmed_fetcher.py          # PubMed API integration
├── processors/
│   └── keyword_matcher.py         # Keyword matching & relevance scoring
├── services/
│   ├── settings_service.py        # Settings load/save/backup
│   └── export_service.py          # CSV export
├── storage/
│   └── data_storage.py            # Local data persistence
├── utils/
│   ├── constants.py               # Shared constants
│   ├── journal_utils.py           # Journal name utilities
│   └── logger.py                  # Logging
├── frontend/                      # Next.js + TypeScript application
│   ├── package.json               # Next.js 15, React 19, TypeScript 5.7
│   ├── tsconfig.json              # Strict TypeScript config
│   ├── next.config.ts             # Static export (output: "export")
│   ├── tailwind.config.ts         # Tailwind CSS config
│   ├── postcss.config.mjs         # PostCSS + Autoprefixer
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx         # Root layout
│   │   │   ├── page.tsx           # Main page & tab navigation
│   │   │   └── globals.css        # Tailwind directives
│   │   ├── components/
│   │   │   ├── PapersTab.tsx      # Papers view with sidebar controls
│   │   │   ├── PaperCard.tsx      # Individual paper display
│   │   │   ├── Statistics.tsx     # Paper statistics
│   │   │   ├── ModelsTab.tsx      # Model preset management
│   │   │   └── SettingsTab.tsx    # Settings management
│   │   ├── lib/
│   │   │   └── api.ts             # Typed API client
│   │   └── types/
│   │       └── index.ts           # Shared TypeScript interfaces
│   └── out/                       # Built static files (auto-generated)
├── logs/                          # Application logs
├── KB_alz/                        # Knowledge base PDFs
├── docs/                          # Documentation
└── scripts/                       # Utility scripts
    └── legacy/                    # Legacy scripts
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/settings` | Get current settings |
| `PUT` | `/api/settings` | Save settings |
| `POST` | `/api/papers/fetch` | Fetch and rank papers |
| `POST` | `/api/papers/export` | Export papers as CSV |
| `GET` | `/api/models` | List saved model presets |
| `POST` | `/api/models` | Save a new model preset |
| `POST` | `/api/models/{filename}/load` | Load a model preset |
| `GET` | `/api/models/{filename}/preview` | Preview a model preset |
| `DELETE` | `/api/models/{filename}` | Delete a model preset |
| `GET` | `/api/backups` | List settings backups |
| `POST` | `/api/backups/create` | Create a settings backup |
| `POST` | `/api/backups/restore` | Restore a settings backup |
| `DELETE` | `/api/backups` | Delete a settings backup |

---

## Troubleshooting

### Common Issues

**"npm: command not found"**
```bash
# Install Node.js into your Conda environment
conda install nodejs -y
```

**"Module not found" (Python)**
```bash
conda activate basic
pip install -r requirements.txt
```

**Port 8000 already in use**
```bash
lsof -i :8000
kill -9 <PID>
```

**Frontend not displaying**
```bash
# Force a rebuild
cd frontend && npm run build
# Then restart
cd .. && python server.py
```

### Logs and Debugging

- Application logs are written to `logs/app.log`
- The server outputs to the terminal — check there for startup errors
- API docs are available at `http://localhost:8000/docs` (Swagger UI)

---

## License

This project is open source, but not for commercial use. Buy me a coffee when we meet.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs in the terminal and `logs/app.log`
3. Create an issue in the project repository

---

**Note**: This app requires an internet connection to fetch papers from the various APIs.
