# Manuscript Alert System for AD and Neuroimaging

A local web application that helps researchers stay updated with the latest papers in Alzheimer's disease and neuroimaging from PubMed, arXiv, bioRxiv, and medRxiv.

---

## Tested on Mac and Linux with Conda

## Quick Start

**Prerequisites:** Python 3.10+ and Node.js 18+ (both included if using the Conda setup below).

```bash
conda activate manuscript_alert
python server.py
```

The server will:

1. Install frontend dependencies (if needed)
2. Build the React frontend (if needed)
3. Start the application at **[http://localhost:8000](http://localhost:8000)**

Papers from all sources (arXiv, bioRxiv, medRxiv, PubMed) are fetched automatically on startup.

To stop the server, press `Ctrl+C`. To deactivate the conda environment:

```bash
conda deactivate
```

### Development Mode

If you're working on the frontend separately with the Next.js dev server:

```bash
# Terminal 1: Start the API server (skip frontend build)
conda activate manuscript_alert
python server.py --dev

# Terminal 2: Start Next.js dev server with hot reload
cd frontend && npm run dev
```

---

## Running Remotely

If you are running the app on a remote server (e.g., via SSH), use one of the following methods:

**Option 1: SSH Port Forwarding (Recommended)**

```bash
ssh -L 8000:localhost:8000 your_username@remote_server_ip
```

Then open [http://localhost:8000](http://localhost:8000) in your local browser.

**Option 2: Access via Network**

The server binds to `0.0.0.0`, so it is accessible on all network interfaces. Open `http://<server_ip>:8000` and make sure port 8000 is allowed through the firewall:

```bash
sudo ufw allow 8000
```

> **Note:** Exposing the app to the internet can have security implications. SSH port forwarding is safer for most users.

---

## Features

- **Multi-source paper fetching**: PubMed, arXiv, bioRxiv, and medRxiv
- **Auto-fetch on startup**: Papers are fetched automatically when the app loads
- **Smart keyword matching**: Papers must match at least 2 keywords to be displayed
- **Relevance scoring**: Papers are ranked by relevance to your research interests
- **Journal quality filtering**: Option to show only papers from high-impact journals
- **Paper archiving**: Save interesting papers for later reference
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

**Option A: Use the bootstrap script** (creates env, installs deps automatically):

```bash
source scripts/bootstrap_conda_env.sh
```

**Option B: Manual setup**:

1. **Create and activate conda environment**:
  ```bash
   conda create -n manuscript_alert python=3.11 nodejs -y
   conda activate manuscript_alert
  ```
2. **Install Python dependencies**:
  ```bash
   pip install -r requirements.txt
  ```
3. To deactivate when done:
  ```bash
   conda deactivate
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
  - Archive papers for later
  - Export to CSV
2. **Models Tab**: Save/load keyword & settings presets for different research topics. Two presets ship by default: `AD_neuroimaging` and `Stroke_imaging`.
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

Backend Architecture

- **Frontend**: Next.js 16 + React 19 + TypeScript 5.9 + Tailwind CSS 4
- **Backend**: FastAPI (Python 3.10+) with modular routers, Pydantic models, REST API
- **Data Sources**: PubMed, arXiv, bioRxiv/medRxiv APIs (parallel fetch)
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
├── server.py                      # Thin entry point (imports backend)
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Ruff configuration
├── backend/
│   ├── src/                       # All Python code lives here
│   │   ├── main.py                # App factory, CORS, routers, static serving
│   │   ├── config.py              # Paths, singletons, shared state
│   │   ├── api/                   # Route modules
│   │   │   ├── health.py          # GET /api/health
│   │   │   ├── settings.py        # Settings GET/PUT
│   │   │   ├── papers.py          # Fetch, export, archive
│   │   │   ├── models.py          # Model preset CRUD
│   │   │   └── backups.py         # Backup CRUD
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── paper_service.py   # Fetch & rank, journal scoring
│   │   │   ├── archive_service.py # Archive JSON I/O
│   │   │   ├── settings_service.py# Settings load/save/backup
│   │   │   └── export_service.py  # CSV/JSON/BibTeX export
│   │   ├── fetchers/              # External API integrations
│   │   │   ├── arxiv_fetcher.py
│   │   │   ├── biorxiv_fetcher.py
│   │   │   └── pubmed_fetcher.py
│   │   ├── processors/
│   │   │   └── keyword_matcher.py # Keyword matching & relevance scoring
│   │   └── utils/
│   │       ├── constants.py       # Shared constants
│   │       ├── journal_utils.py   # Journal name utilities
│   │       └── logger.py          # Logging
│   ├── config/
│   │   ├── settings.py            # Current application settings
│   │   ├── models/                # Saved model presets (JSON)
│   │   └── backups/               # Settings backups (gitignored)
│   └── data/
│       └── archive/               # Archived papers (JSON)
├── frontend/                      # Next.js + TypeScript application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx         # Root layout
│   │   │   ├── page.tsx           # Main page & tab navigation
│   │   │   └── globals.css        # Tailwind imports & custom styles
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
├── docs/                          # Documentation & diagrams
├── scripts/                       # Utility scripts
├── KB_alz/                        # Knowledge base PDFs
└── logs/                          # Application logs
```

### API Endpoints


| Method   | Endpoint                         | Description                 |
| -------- | -------------------------------- | --------------------------- |
| `GET`    | `/api/health`                    | Health check                |
| `GET`    | `/api/settings`                  | Get current settings        |
| `PUT`    | `/api/settings`                  | Save settings               |
| `POST`   | `/api/papers/fetch`              | Fetch and rank papers       |
| `POST`   | `/api/papers/export`             | Export papers as CSV        |
| `POST`   | `/api/papers/archive`            | Archive a paper             |
| `GET`    | `/api/papers/archive`            | List archived papers        |
| `DELETE` | `/api/papers/archive`            | Remove a paper from archive |
| `GET`    | `/api/models`                    | List saved model presets    |
| `POST`   | `/api/models`                    | Save a new model preset     |
| `POST`   | `/api/models/{filename}/load`    | Load a model preset         |
| `GET`    | `/api/models/{filename}/preview` | Preview a model preset      |
| `DELETE` | `/api/models/{filename}`         | Delete a model preset       |
| `GET`    | `/api/backups`                   | List settings backups       |
| `POST`   | `/api/backups/create`            | Create a settings backup    |
| `POST`   | `/api/backups/restore`           | Restore a settings backup   |
| `DELETE` | `/api/backups`                   | Delete a settings backup    |


---

## Troubleshooting

### Common Issues

**"npm: command not found"**

```bash
conda install nodejs -y
```

**"Module not found" (Python)**

```bash
conda activate manuscript_alert
pip install -r requirements.txt
```

**Port 8000 already in use**

```bash
lsof -i :8000
kill -9 <PID>
```

**Frontend not displaying**

```bash
rm -rf frontend/out
python server.py   # will rebuild automatically
```

### Clean Reinstall

```bash
conda activate manuscript_alert
pip install --force-reinstall -r requirements.txt
rm -rf frontend/node_modules frontend/out
python server.py   # will reinstall and rebuild automatically
```

### Stopping and Restarting

- To stop: Press `Ctrl+C` in the terminal
- To restart: `python server.py` (frontend is only rebuilt when source files have changed)

### Logs and Debugging

- Application logs are written to `logs/app.log`
- The server outputs to the terminal — check there for startup errors
- API docs are available at `http://localhost:8000/docs` (Swagger UI)

---

## Roadmap

See [docs/cloud_migration_plan.md](docs/cloud_migration_plan.md) for the cloud migration roadmap and [docs/architecture_reference.md](docs/architecture_reference.md) for detailed technical reference.

---

## License

This project is open source, but not for commercial use.

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the logs in the terminal and `logs/app.log`
3. Create an issue in the project repository

---

**Note**: This app requires an internet connection to fetch papers from the various APIs.