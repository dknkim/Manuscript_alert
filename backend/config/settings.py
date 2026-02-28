"""
Settings configuration for the Manuscript Alert System.
This file contains all configurable settings that can be modified through the UI.
"""

# Default keywords for research alerts
DEFAULT_KEYWORDS = [
    "Alzheimer's disease",
    "PET",
    "amyloid",
    "tau",
    "plasma",
    "brain",
    "MRI",
]

# Journal scoring configuration
JOURNAL_SCORING = {
    "enabled": True,
    "high_impact_journal_boost": {
        "5_or_more_keywords": 4.9,
        "4_keywords": 3.7,
        "3_keywords": 2.8,
        "2_keywords": 0.9999999999999999,
        "1_keyword": 0.10000000000000003,
    },
}

# Target journal patterns with priority levels
TARGET_JOURNALS = {
    "exact_matches": [
        "jama",
        "nature",
        "science",
        "radiology",
        "ajnr",
        "the lancet",
    ],
    "family_matches": [
        "jama",
        "nature",
        "science",
        "npj",
        "the lancet",
    ],
    "specific_journals": [
        "american journal of neuroradiology",
        "alzheimer's & dementia",
        "alzheimers dement",
        "ebiomedicine",
        "journal of magnetic resonance imaging",
        "magnetic resonance in medicine",
        "radiology",
        "jmri",
        "j magn reson imaging",
        "brain : a journal of neurology",
    ],
}

# Simplified journal exclusions - all patterns apply to all journal types
JOURNAL_EXCLUSIONS = [
    "abdominal",
    "pediatric",
    "cardiovascular and interventional",
    "interventional",
    "skeletal",
    "clinical",
    "academic",
    "investigative",
    "case reports",
    "oral surgery",
    "korean journal of",
    "the neuroradiology",
    "japanese journal of",
    "brain research",
    "brain and behavior",
    "brain imaging and behavior",
    "brain stimulation",
    "brain and cognition",
    "brain, behavior, and immunity",
    "metabolic brain disease",
    "neuroscience letters",
    "neuroscience bulletin",
    "neuroscience methods",
    "neuroscience research",
    "neuroscience and biobehavioral",
    "clinical neuroscience",
    "neuropsychiatry",
    "ibro neuroscience",
    "acs chemical neuroscience",
    "proceedings of the national academy",
    "life science alliance",
    "life sciences",
    "animal science",
    "veterinary medical science",
    "philosophical transactions",
    "annals of the new york academy",
]

# Keyword-specific scoring (for future enhancement)
KEYWORD_SCORING = {
    "high_priority": {
        "keywords": [
            "Alzheimer's disease",
            "amyloid",
            "tau",
        ],
        "boost": 1.5,
    },
    "medium_priority": {
        "keywords": [
            "PET",
            "brain",
            "plasma",
            "MRI",
        ],
        "boost": 1.2,
    },
}

# Must-have keywords (required filter - papers must match at least one)
MUST_HAVE_KEYWORDS = []

# Default search settings
DEFAULT_SEARCH_SETTINGS = {
    "days_back": 8,
    "search_mode": "Brief",
    "min_keyword_matches": 2,
    "max_results_display": 50,
    "default_sources": {
        "pubmed": True,
        "arxiv": False,
        "biorxiv": True,
        "medrxiv": True,
    },
    "journal_quality_filter": False,
}

# UI settings
UI_SETTINGS = {
    "theme": "light",
    "show_abstracts": True,
    "show_keywords": True,
    "show_relevance_scores": True,
    "papers_per_page": 50,
}
