# Knowledge Base System for Manuscript Alert

This system creates a knowledge base of the top 20 articles for each of the past 4 weeks, leveraging the existing Manuscript Alert infrastructure for fetching and ranking papers.

## Files Created

### 1. `knowledge_base_builder.py`
The main script that builds the knowledge base by:
- Fetching papers from arXiv, bioRxiv, medRxiv, and PubMed
- Ranking papers by relevance using the existing keyword matching system
- Selecting the top 20 papers per week for the past 4 weeks
- Saving the results in structured JSON format

### 2. `knowledge_base_analyzer.py`
A utility script to analyze and explore the generated knowledge base:
- Provides comprehensive statistics and insights
- Allows searching through papers
- Exports data to CSV format
- Generates detailed reports

## Usage

### Building a Knowledge Base

```bash
# Activate the conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate basic

# Run the knowledge base builder
python knowledge_base_builder.py
```

This will create a JSON file named `knowledge_base_YYYYMMDD_HHMMSS.json` containing:
- Metadata about the knowledge base
- Weekly breakdowns with top 20 papers per week
- Complete paper information including titles, abstracts, authors, relevance scores, etc.

### Analyzing the Knowledge Base

```bash
# Analyze a specific knowledge base file
python knowledge_base_analyzer.py knowledge_base_20250915_204225.json
```

This will provide:
- Basic statistics (total papers, weeks covered, etc.)
- Source distribution (PubMed, arXiv, etc.)
- Journal distribution
- Keyword analysis
- Relevance score analysis
- Top papers by relevance
- CSV export of all data

## Knowledge Base Structure

The generated JSON file has the following structure:

```json
{
  "metadata": {
    "created_at": "2025-09-15T20:39:45.346306",
    "weeks_covered": 4,
    "keywords_used": ["Alzheimer's disease", "PET", "MRI", ...],
    "data_sources": {"arxiv": true, "biorxiv": true, ...},
    "search_mode": "Extended",
    "total_papers": 80,
    "papers_per_week": 20
  },
  "weeks": {
    "week_1": {
      "week_info": {
        "week_number": 1,
        "start_date": "2025-09-09 00:00:00",
        "end_date": "2025-09-15 00:00:00",
        "week_label": "Week 1 (2025-09-09 to 2025-09-15)"
      },
      "papers": [
        {
          "title": "Paper title",
          "authors": "Author list",
          "abstract": "Paper abstract",
          "published": "2025-09-10",
          "source": "PubMed",
          "relevance_score": 10.5,
          "matched_keywords": ["Alzheimer's disease", "amyloid", ...],
          "journal": "Nature aging",
          "arxiv_url": "https://pubmed.ncbi.nlm.nih.gov/...",
          "pmid": "40931114",
          "doi": "10.1038/...",
          "categories": ["PubMed", "MeSH terms"]
        }
      ],
      "paper_count": 20
    }
  }
}
```

## Key Features

### Comprehensive Data Sources
- **PubMed**: Peer-reviewed medical literature
- **arXiv**: Preprints in physics, mathematics, computer science
- **bioRxiv**: Biology preprints
- **medRxiv**: Medical preprints

### Intelligent Ranking
- Uses the existing keyword matching system from the main app
- Boosts scores for high-impact journals (Nature, JAMA, Science, etc.)
- Considers keyword frequency and title matches
- Ranks by relevance score to ensure quality

### Rich Metadata
Each paper includes:
- Title, authors, abstract
- Publication date and journal information
- Relevance score and matched keywords
- URLs (PubMed, arXiv, DOI)
- Source and categories

## Sample Results

From the latest run:
- **Total Papers**: 80 (20 per week × 4 weeks)
- **Source Distribution**: 76 PubMed, 3 medRxiv, 1 arXiv
- **Top Journals**: Journal of Alzheimer's Disease, Alzheimer's & Dementia, Brain
- **Average Relevance Score**: 6.6
- **Keyword Coverage**: 100% of papers matched at least 2 keywords

## Future RAG Integration

This knowledge base is designed to be easily integrated with RAG (Retrieval-Augmented Generation) systems:

1. **Structured Data**: JSON format makes it easy to parse and index
2. **Rich Content**: Abstracts and titles provide good text for embedding
3. **Metadata**: Keywords, scores, and journal info enable filtering
4. **Temporal Organization**: Weekly structure allows time-based queries
5. **CSV Export**: Alternative format for different RAG implementations

## Customization

You can modify the knowledge base builder to:
- Change the number of weeks to cover
- Adjust the number of papers per week
- Modify keywords or data sources
- Change the ranking algorithm
- Add additional metadata fields

## Requirements

- Python 3.7+
- All dependencies from the main Manuscript Alert system
- Internet connection for API calls
- Sufficient disk space for JSON files (typically 100-200KB per knowledge base)

## Notes

- The system respects API rate limits for all sources
- PubMed has the most comprehensive coverage for medical topics
- arXiv and bioRxiv provide early access to cutting-edge research
- The ranking system prioritizes papers with multiple keyword matches
- High-impact journals receive score boosts to ensure quality
