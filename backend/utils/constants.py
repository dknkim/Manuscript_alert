"""Constants used throughout the application."""

# Color scheme for relevance scores (quartile-based)
RELEVANCE_COLORS = {
    "excellent": "#00c851",  # Green for top quartile (7.5+)
    "good": "#ffbb33",  # Amber for upper-middle quartile (5-7.4)
    "average": "#ff8800",  # Dark Orange for lower-middle quartile (2.5-4.9)
    "poor": "#cc0000",  # Red for bottom quartile (<2.5)
}

# Relevance score thresholds
RELEVANCE_THRESHOLDS = {"excellent": 7.5, "good": 5.0, "average": 2.5}

# Golden border style for high-impact papers
HIGH_IMPACT_STYLE = """
    border: 3px solid #B8860B !important;
    border-radius: 12px !important;
    background: linear-gradient(135deg,
        rgba(184, 134, 11, 0.03), rgba(184, 134, 11, 0.08)) !important;
    box-shadow: 0 4px 8px rgba(184, 134, 11, 0.2) !important;
"""

# Search modes
SEARCH_MODES = {
    "Standard (Balanced)": "Standard",
    "Brief (Quick scan, ~30 papers max per source)": "Brief",
    "Extended (Comprehensive, ~100 papers max per source)": "Extended",
}

# Default configuration
DEFAULT_CONFIG = {
    "days_back": 7,
    "search_mode": "Standard (Balanced)",
    "min_keyword_matches": 2,
    "max_display_papers": 50,
}

# API limits per source
API_LIMITS = {
    "standard": {"max_papers": 50},
    "brief": {"max_papers": 30},
    "extended": {"max_papers": 100},
}

# Source metadata
SOURCE_INFO = {
    "pubmed": {
        "name": "PubMed",
        "icon": "🏥",
        "description": "Peer-reviewed biomedical literature",
    },
    "arxiv": {
        "name": "arXiv",
        "icon": "📚",
        "description": "Preprint repository for scientific papers",
    },
    "biorxiv": {
        "name": "bioRxiv",
        "icon": "🧬",
        "description": "Preprint server for biology",
    },
    "medrxiv": {
        "name": "medRxiv",
        "icon": "⚕️",
        "description": "Preprint server for health sciences",
    },
}
