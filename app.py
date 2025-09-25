import concurrent.futures
import json
import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from fetchers.arxiv_fetcher import ArxivFetcher
from fetchers.biorxiv_fetcher import BioRxivFetcher
from fetchers.pubmed_fetcher import PubMedFetcher
from processors.keyword_matcher import KeywordMatcher
from storage.data_storage import DataStorage

# RAG imports
try:
    from rag.rag_system import RAGSystem
    from rag.llm_client import LLMFactory
    RAG_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ RAG system not available: {e}")
    RAG_AVAILABLE = False


# Set page configuration
st.set_page_config(
    page_title="Manuscript Alert System for AD and Neuroimaging",
    # page_icon="📚",
    layout="wide",
)


# Initialize components
@st.cache_resource
def initialize_components():
    return (
        ArxivFetcher(),
        BioRxivFetcher(),
        PubMedFetcher(),
        KeywordMatcher(),
        DataStorage(),
    )

# Initialize RAG system
@st.cache_resource
def initialize_rag_system():
    """Initialize RAG system if available"""
    if RAG_AVAILABLE:
        return RAGSystem()
    return None


(arxiv_fetcher, biorxiv_fetcher, pubmed_fetcher, keyword_matcher, data_storage) = (
    initialize_components()
)

# Default keywords
DEFAULT_KEYWORDS = [
    "Alzheimer's disease",
    "PET",
    "MRI",
    "dementia",
    "amyloid",
    "tau",
    "plasma",
    "brain",
]


def main():
    st.title("Manuscript Alert System for AD and Neuroimaging")
    st.markdown(
        "Stay updated with the latest Pubmed, arXiv, biorXiv, "
        "and medrXiv papers in DK's field of interest"
    )
    
    # Create tabs
    if RAG_AVAILABLE:
        tab1, tab2 = st.tabs(["📚 Paper Discovery", "🔍 Research Assistant"])
    else:
        tab1 = st.container()
        tab2 = None

    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")

        # Load user preferences
        preferences = data_storage.load_preferences()

        # Keywords configuration
        st.subheader("Keywords")

        # Load existing keywords or use defaults
        current_keywords = preferences.get("keywords", DEFAULT_KEYWORDS)

        # Text area for keywords input
        keywords_text = st.text_area(
            "Enter keywords (one per line):",
            value="\n".join(current_keywords),
            height=150,
            help="Enter research topics you're interested in, one per line. "
            "Papers must match at least 2 keywords to be displayed.",
        )

        # Parse keywords from text area
        keywords = [k.strip() for k in keywords_text.split("\n") if k.strip()]

        # Save preferences button
        if st.button("💾 Save Keywords"):
            preferences["keywords"] = keywords
            data_storage.save_preferences(preferences)
            st.success("Keywords saved!")
            st.rerun()

        # Journal Quality Filter
        st.subheader("Journal Quality")
        show_high_impact_only = st.checkbox(
            "🌟 Relevant Journals Only",
            value=False,
            help="Show only papers from: Nature/JAMA/NPJ/Science journals, "
            "Radiology, AJNR, Brain, MRM, JMRI, and Alzheimer's & Dementia",
        )

        # Date range selection (moved here before KB creation)
        st.subheader("Date Range")
        days_back = st.slider(
            "Days to look back:",
            min_value=1,
            max_value=21,
            value=7,
            help="Number of days to search back from today",
        )

        # Search limit selection
        st.subheader("Search Limits")
        search_mode = st.radio(
            "Article search limit:",
            [
                "Brief (PubMed: 1000, Others: 500)",
                "Standard (PubMed: 2500, Others: 1000)",
                "Extended (All sources: 5000)",
            ],
            index=0,
            help="Choose search depth vs speed trade-off",
        )

        if search_mode.startswith("Extended"):
            st.caption(
                "⚠️ Extended mode may take 2-3x longer but provides "
                "comprehensive results."
            )
        elif search_mode.startswith("Standard"):
            st.caption("⚠️ Standard mode balanced for speed and coverage.")
        else:
            st.caption("⚠️ Brief mode optimized for fastest results with recent papers.")

        # Data sources selection
        st.subheader("Data Sources")
        col1, col2 = st.columns(2)

        with col1:
            use_arxiv = st.checkbox(
                "arXiv", value=False, help="Include papers from arXiv"
            )
            use_biorxiv = st.checkbox(
                "bioRxiv", value=False, help="Include papers from bioRxiv"
            )
        with col2:
            use_medrxiv = st.checkbox(
                "medRxiv", value=False, help="Include papers from medRxiv"
            )
            use_pubmed = st.checkbox(
                "PubMed", value=True, help="Include papers from PubMed"
            )

        # Refresh data
        st.subheader("Data Management")
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            # Also clear any file-based cache
            if os.path.exists("paper_cache.json"):
                os.remove("paper_cache.json")
            st.success("All caches cleared! Data will be refreshed.")
            st.rerun()
        
        # Knowledge Base Creation
        st.subheader("🧠 Knowledge Base")
        if st.button("📚 Create Top 20 KB", help="Create a knowledge base with papers that have relevance score > 4.0 ONLY (up to 20 papers)"):
            # Get current configuration
            current_data_sources = {
                "arxiv": use_arxiv,
                "biorxiv": use_biorxiv,
                "medrxiv": use_medrxiv,
                "pubmed": use_pubmed,
            }
            
            # Create the knowledge base using currently displayed papers
            kb_filepath = create_top_papers_knowledge_base(
                keywords=keywords,
                data_sources=current_data_sources,
                search_mode=search_mode,
                days_back=days_back
            )
            
            if kb_filepath:
                st.balloons()  # Celebration animation
                st.success("🎉 Knowledge base created successfully!")
            else:
                st.error("❌ Failed to create knowledge base. Please try again.")
        
        # Show existing KB files
        kb_dir = "./KB"
        if os.path.exists(kb_dir):
            kb_files = [f for f in os.listdir(kb_dir) if f.endswith('.json')]
            if kb_files:
                st.caption(f"📁 {len(kb_files)} KB file(s) in ./KB/")
                # Show the most recent file
                kb_files.sort(reverse=True)
                latest_file = kb_files[0]
                st.caption(f"Latest: {latest_file}")
            else:
                st.caption("📁 No KB files found in ./KB/")
        else:
            st.caption("📁 KB directory will be created when needed")

    # Paper Discovery Tab
    with tab1:
        # Main content area
        # Since Streamlit doesn't support right sidebars or sticky columns natively,
        # we'll use the column layout with expandable sections for better organization
        col1, col2 = st.columns([3, 1])

    with col1:
        st.header("Recent Papers")

        # Display current keywords
        if keywords:
            st.info(
                f"**Active Keywords:** {', '.join(keywords[:5])}"
                + (f" and {len(keywords) - 5} more..." if len(keywords) > 5 else "")
            )
        else:
            st.warning(
                "No keywords configured. Please add some keywords in the sidebar."
            )
            return

        # Create data sources dict
        data_sources = {
            "arxiv": use_arxiv,
            "biorxiv": use_biorxiv,
            "medrxiv": use_medrxiv,
            "pubmed": use_pubmed,
        }

        # Check if at least one source is selected
        if not any(data_sources.values()):
            st.warning("Please select at least one data source in the sidebar.")
            return

        # Fetch and process papers with progress indicators
        source_names = [k for k, v in data_sources.items() if v]

        # Show compact loading indicator
        if source_names:
            with st.container():
                loading_placeholder = st.empty()
                loading_placeholder.info("🔄 Fetching papers from " + ", ".join([s.upper() for s in source_names]) + "...")

                # Normalize end_date to current day to make cache more predictable
                end_date_normalized = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

                # Fetch papers (the actual fetching happens inside the cached function)
                papers = fetch_and_rank_papers(
                    keywords, days_back, data_sources, end_date_normalized, search_mode
                )

                # Clear loading and show compact success message
                loading_placeholder.empty()
                if not papers.empty:
                    st.success(f"🎉 Found {len(papers)} papers from {len(source_names)} {'source' if len(source_names) == 1 else 'sources'}")
        else:
            # Fallback if no sources selected
            papers = pd.DataFrame()

        if papers.empty:
            st.warning("No papers found for the specified keywords and date range.")
            return

        # Search within results
        search_query = st.text_input(
            "🔍 Search within results:", placeholder="Enter search term..."
        )

        # Apply filters
        filtered_papers = papers.copy()

        # Search filter
        if search_query:
            filtered_papers = filtered_papers[
                filtered_papers["title"].str.contains(
                    search_query, case=False, na=False
                )
                | filtered_papers["abstract"].str.contains(
                    search_query, case=False, na=False
                )
                | filtered_papers["authors"].str.contains(
                    search_query, case=False, na=False
                )
            ]

        # Relevant journal filter
        if show_high_impact_only:
            high_impact_mask = filtered_papers.apply(
                lambda row: (
                    row.get("source") == "PubMed"
                    and row.get("journal")
                    and is_high_impact_journal(row["journal"])
                ),
                axis=1,
            )
            filtered_papers = filtered_papers[high_impact_mask]

        # Filter papers with at least 2 matched keywords
        keyword_filter_mask = filtered_papers.apply(
            lambda row: len(row.get("matched_keywords", [])) >= 2, axis=1
        )
        filtered_papers = filtered_papers[keyword_filter_mask]

        # Display results count
        st.markdown(
            f"**Found {len(filtered_papers)} papers** "
            f"(showing top {min(len(filtered_papers), 50)})"
        )

        if len(filtered_papers) < len(papers):
            excluded_count = len(papers) - len(filtered_papers)
            st.caption(
                f"Note: {excluded_count} papers excluded "
                f"(require minimum 2 matched keywords)"
            )

        # Warning for large date ranges
        if days_back > 14:
            total_fetched = len(papers)
            if total_fetched >= 5000:  # Close to extended API limits
                st.warning(
                    f"⚠️ Large date range ({days_back} days) may hit API limits. "
                    "Consider reducing the date range or using more specific "
                    "keywords if you suspect missing papers."
                )

        # Display papers
        display_papers(filtered_papers.head(50))

    # Statistics panel with expandable sections
    with col2:
        st.header("📊 Statistics")

        if not papers.empty:
            # Summary statistics in expandable section
            with st.expander("📈 Overview", expanded=True):
                st.metric("Total Papers", len(papers))
                try:
                    avg_score = float(papers["relevance_score"].mean())
                    max_score = float(papers["relevance_score"].max())
                    st.metric("Avg Relevance Score", f"{avg_score:.1f}")
                    st.metric("Max Relevance Score", f"{max_score:.0f}")
                except Exception:
                    st.metric("Avg Relevance Score", "N/A")
                    st.metric("Max Relevance Score", "N/A")

            # Source distribution in expandable section
            with st.expander("📊 Sources", expanded=True):
                source_counts = papers["source"].value_counts()
                for source, count in source_counts.items():
                    st.write(f"• **{source}**: {count}")

            # Target journals count
            high_impact_count = 0
            for _, paper in papers.iterrows():
                if paper.get("source") == "PubMed" and paper.get("journal"):
                    journal_name = paper["journal"]
                    if is_high_impact_journal(journal_name):
                        high_impact_count += 1

            if high_impact_count > 0:
                with st.expander("🏆 Journal Quality", expanded=True):
                    st.metric("Relevant Journals", high_impact_count)

            # Top keywords found in expandable section
            with st.expander("🔍 Keywords", expanded=False):
                keyword_counts = {}
                for _, paper in papers.iterrows():
                    for kw in paper["matched_keywords"]:
                        keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

                if keyword_counts:
                    top_keywords = sorted(
                        keyword_counts.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]
                    for kw, count in top_keywords:
                        st.write(f"• **{kw}**: {count}")

            # Debug section in expandable section
            with st.expander("🔧 Debug Info", expanded=False):
                all_journals = set()
                target_journals_found = set()

                for _, paper in papers.iterrows():
                    if (paper.get("source") == "PubMed" and
                        paper.get("journal")):
                        journal = paper["journal"].lower()
                        all_journals.add(journal)
                        if is_high_impact_journal(paper["journal"]):
                            target_journals_found.add(journal)

                st.write("**Target Journals Found:**")
                for journal in sorted(target_journals_found):
                    st.write(f"• {journal}")

                st.write("**All Journals (first 20):**")
                for journal in sorted(all_journals)[:20]:
                    st.write(f"• {journal}")

            # Export functionality in expandable section
            with st.expander("📥 Export", expanded=True):
                # Generate dynamic filename based on actual sources used
                if not papers.empty:
                    # Get unique sources from the papers dataframe
                    actual_sources = papers["source"].unique() if "source" in papers.columns else []

                    # Map source names to lowercase for filename
                    source_mapping = {
                        "PubMed": "pubmed",
                        "arXiv": "arxiv",
                        "bioRxiv": "biorxiv",
                        "medRxiv": "medrxiv"
                    }

                    # Create source string for filename
                    sources_for_filename = []
                    for source in actual_sources:
                        mapped = source_mapping.get(source, source.lower())
                        sources_for_filename.append(mapped)

                    # Sort for consistent ordering
                    sources_for_filename.sort()
                    sources_str = "_".join(sources_for_filename) if sources_for_filename else "papers"

                    # Add filtered indicator if papers were filtered
                    filtered_suffix = f"_filtered{len(filtered_papers)}" if len(filtered_papers) < len(papers) else ""

                    # Generate filename with date
                    export_filename = f"{sources_str}{filtered_suffix}_{datetime.now().strftime('%Y%m%d')}.csv"

                    # Display export information first
                    st.caption(f"Filename: {export_filename}")
                    st.caption(f"Contains {len(filtered_papers)} papers from {', '.join(actual_sources)}")

                    # Export only the filtered papers that are displayed
                    csv = filtered_papers.to_csv(index=False)
                    st.download_button(
                        label="📥 Filtered Results",
                        data=csv,
                        file_name=export_filename,
                        mime="text/csv",
                    )
    
    # RAG Assistant Tab
    if RAG_AVAILABLE and tab2 is not None:
        with tab2:
            render_rag_interface()


@st.cache_data(ttl=600)  # Cache for 10 minutes for faster updates
def fetch_and_rank_papers(
    keywords, days_back, data_sources, end_date=None, search_mode="Standard"
):
    """Fetch papers from multiple sources and rank them by keyword relevance"""

    # Calculate date range - use passed end_date or current time
    if end_date is None:
        end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    all_papers_data = []

    # Set search limits based on mode
    brief_mode = search_mode.startswith("Brief")
    extended_mode = search_mode.startswith("Extended")

    # Define fetching functions for parallel execution
    def fetch_arxiv():
        if data_sources.get("arxiv", False):
            try:
                return (
                    "arxiv",
                    arxiv_fetcher.fetch_papers(
                        start_date, end_date, keywords, brief_mode, extended_mode
                    ),
                )
            except Exception as e:
                return ("arxiv_error", str(e))
        return ("arxiv", [])

    def fetch_biorxiv():
        if data_sources.get("biorxiv", False) or data_sources.get("medrxiv", False):
            try:
                biorxiv_papers = biorxiv_fetcher.fetch_papers(
                    start_date, end_date, keywords, brief_mode, extended_mode
                )
                # Filter by source selection
                filtered_papers = []
                for paper in biorxiv_papers:
                    source = paper.get("source", "")
                    if (source == "biorxiv" and data_sources.get("biorxiv", False)) or (
                        source == "medrxiv" and data_sources.get("medrxiv", False)
                    ):
                        filtered_papers.append(paper)
                return ("biorxiv", filtered_papers)
            except Exception as e:
                return ("biorxiv_error", str(e))
        return ("biorxiv", [])

    def fetch_pubmed():
        if data_sources.get("pubmed", False):
            try:
                return (
                    "pubmed",
                    pubmed_fetcher.fetch_papers(
                        start_date, end_date, keywords, brief_mode, extended_mode
                    ),
                )
            except Exception as e:
                return ("pubmed_error", str(e))
        return ("pubmed", [])

    # Execute all API calls in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(fetch_arxiv),
            executor.submit(fetch_biorxiv),
            executor.submit(fetch_pubmed),
        ]

        # Collect results
        for future in concurrent.futures.as_completed(futures):
            result_type, result_data = future.result()

            if result_type.endswith("_error"):
                source_name = result_type.replace("_error", "")
                st.error(f"Error fetching from {source_name}: {result_data}")
            else:
                all_papers_data.extend(result_data)

    if not all_papers_data:
        return pd.DataFrame()

    # Define processing function for parallel execution
    def process_paper(paper):
        relevance_score, matched_keywords = keyword_matcher.calculate_relevance(
            paper, keywords
        )

        # Boost score for target journals (only if at least 2 keywords matched)
        if paper.get("source") == "PubMed" and paper.get("journal"):
            # if is_high_impact_journal(
            #         paper['journal']) and len(matched_keywords) >= 2:
            #     relevance_score += 3.0  # Boost target journal papers
            #     # with sufficient keyword matches
            if is_high_impact_journal(paper["journal"]):
                if len(matched_keywords) >= 5:
                    relevance_score += 5.1
                elif 5 > len(matched_keywords) >= 4:
                    relevance_score += 3.7
                elif 4 > len(matched_keywords) >= 3:
                    relevance_score += 2.8
                elif 3 > len(matched_keywords) >= 2:
                    relevance_score += 1.3

        # Format authors list
        authors = paper.get("authors", [])
        if isinstance(authors, list):
            authors_str = ", ".join(authors[:3]) + ("..." if len(authors) > 3 else "")
        else:
            authors_str = str(authors)

        return (paper, relevance_score, matched_keywords, authors_str)

    # Process papers in parallel for faster ranking
    ranked_papers = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_paper = {
            executor.submit(process_paper, paper): paper for paper in all_papers_data
        }

        for future in concurrent.futures.as_completed(future_to_paper):
            try:
                paper, relevance_score, matched_keywords, authors_str = future.result()

                # Get source information
                source = paper.get("source", "arXiv")
                if source == "PubMed":
                    source_display = "PubMed"
                elif source == "arxiv":
                    source_display = "arXiv"
                else:
                    source_display = source.capitalize()

                paper_info = {
                    "title": paper["title"],
                    "authors": authors_str,
                    "abstract": paper["abstract"],
                    "published": paper["published"],
                    "arxiv_url": paper.get("arxiv_url", ""),
                    "source": source_display,
                    "relevance_score": relevance_score,
                    "matched_keywords": matched_keywords,
                    "journal": paper.get("journal", ""),
                    "volume": paper.get("volume", ""),
                    "issue": paper.get("issue", ""),
                }

                ranked_papers.append(paper_info)
            except Exception:
                continue  # Skip papers that fail processing

    # Convert to DataFrame efficiently and sort by relevance
    df = pd.DataFrame(ranked_papers)
    df = df.sort_values("relevance_score", ascending=False)

    return df


def get_exclusion_patterns():
    """Get patterns for excluding journals from target journal matching"""
    return {
        # Radiology subspecialties - exclude if they contain these specific patterns
        # "radiology_exclusions": [
        #     "abdominal radiology",
        #     "pediatric radiology",
        #     "cardiovascular and interventional radiology",
        #     "interventional radiology",
        #     "emergency radiology",
        #     "skeletal radiology",
        #     "clinical radiology",
        #     "academic radiology",
        #     "investigative radiology",
        #     "case reports",  # This will exclude "radiology case reports"
        #     "oral surgery",  # This will exclude the long oral surgery journal name
        #     "korean journal of radiology",
        #     "the neuroradiology journal",
        #     "interventional neuroradiology",
        #     "japanese journal of radiology",
        # ],
        "radiology_exclusions": [
            "abdominal",
            "pediatric",
            "cardiovascular and interventional",
            "interventional",
            "emergency",
            "skeletal",
            "clinical",
            "academic",
            "investigative",
            "case reports",  # This will exclude "radiology case reports"
            "oral surgery",  # This will exclude the long oral surgery journal name
            "korean journal of",
            "the neuroradiology",
            "interventional",
            "japanese journal of",
        ],
        # Brain subspecialties - exclude these specific patterns
        "brain_exclusions": [
            "brain research",  # Exclude if exact match
            "brain and behavior",
            "brain imaging and behavior",
            "brain stimulation",
            "brain connectivity",
            "brain and cognition",
            "brain, behavior, and immunity",
            "metabolic brain disease",
        ],
        # Neuroscience subspecialties - exclude these patterns
        "neuroscience_exclusions": [
            "neuroscience letters",
            "neuroscience bulletin",
            "neuroscience methods",
            "neuroscience research",
            "neuroscience and biobehavioral",
            "clinical neuroscience",
            "neuropsychiatry",
            "ibro neuroscience",
            "acs chemical neuroscience",
        ],
        # Other exclusions
        "other_exclusions": [
            "proceedings of the national academy",
            "life science alliance",
            "life sciences",
            "animal science",
            "biomaterials science",
            "veterinary medical science",
            "philosophical transactions",
            "annals of the new york academy",
        ],
    }


def is_journal_excluded(journal_name):
    """Check if a journal should be excluded using pattern matching"""
    if not journal_name:
        return False

    journal_lower = journal_name.lower()
    exclusion_patterns = get_exclusion_patterns()

    # Check each category of exclusions
    for category, patterns in exclusion_patterns.items():
        for pattern in patterns:
            pattern_lower = pattern.lower()

            # For radiology, be more specific
            if category == "radiology_exclusions":
                if "radiology" in journal_lower and pattern_lower in journal_lower:
                    # Exception: don't exclude plain "radiology"
                    if journal_lower.strip() == "radiology":
                        continue
                    return True

            # For brain, be more specific
            elif category == "brain_exclusions":
                if "brain" in journal_lower and pattern_lower in journal_lower:
                    # Exception: don't exclude plain "brain"
                    if journal_lower.strip() == "brain":
                        continue
                    return True

            # For other categories, simple pattern matching
            else:
                if pattern_lower in journal_lower:
                    return True

    return False


def is_high_impact_journal(journal_name):
    """Check if a journal is in the user-specified list of target journals"""
    if not journal_name:
        return False

    journal_lower = journal_name.lower().strip()

    # First check if journal should be excluded using pattern matching
    if is_journal_excluded(journal_name):
        return False

    # Define target journal patterns with priority levels
    target_patterns = {
        # High priority - exact matches
        "exact_matches": [
            "jama",
            "nature",
            "science",
            #'brain',
            "radiology",
            "ajnr",
            "the lancet",
        ],
        # Medium priority - specific journal families
        "family_matches": [
            "jama ",  # Space ensures it's part of JAMA family
            "nature ",  # Space ensures it's part of Nature family
            "science ",  # Space ensures it's part of Science family
            "npj ",  # Nature Partner Journals
            "the lancet",
        ],
        # Specific important journals
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
            #'brain',
            "brain : a journal of neurology",
        ],
    }

    # Check exact matches first (highest priority)
    for exact_match in target_patterns["exact_matches"]:
        if journal_lower == exact_match:
            return True

    # Check family matches (medium priority)
    for family_pattern in target_patterns["family_matches"]:
        if journal_lower.startswith(family_pattern):
            return True

    # Check specific journals (lower priority)
    for specific_journal in target_patterns["specific_journals"]:
        if specific_journal in journal_lower:
            return True

    # # Special case for abbreviated forms
    # abbreviations = {
    #     'ajnr': 'american journal of neuroradiology',
    #     'jmri': 'journal of magnetic resonance imaging',
    # }

    # if journal_lower in abbreviations:
    #     return True

    return False


def create_todays_knowledge_base(keywords, data_sources, search_mode="Extended"):
    """
    Create a knowledge base for today's top 20 articles
    
    Args:
        keywords (list): Keywords to search for
        data_sources (dict): Data sources configuration
        search_mode (str): Search mode (Brief/Standard/Extended)
        
    Returns:
        str: Path to the created knowledge base file
    """
    # Create KB directory if it doesn't exist
    kb_dir = "./KB"
    os.makedirs(kb_dir, exist_ok=True)
    
    # Get today's date range
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today
    end_date = today
    
    st.info("🧠 Creating today's knowledge base...")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Fetch papers
    status_text.text("📚 Fetching papers from all sources...")
    progress_bar.progress(20)
    
    all_papers_data = []
    
    # Define fetching functions for parallel execution
    def fetch_arxiv():
        if data_sources.get("arxiv", False):
            try:
                return (
                    "arxiv",
                    arxiv_fetcher.fetch_papers(
                        start_date, end_date, keywords, False, True  # extended_mode=True
                    ),
                )
            except Exception as e:
                return ("arxiv_error", str(e))
        return ("arxiv", [])
    
    def fetch_biorxiv():
        if data_sources.get("biorxiv", False) or data_sources.get("medrxiv", False):
            try:
                papers = biorxiv_fetcher.fetch_papers(
                    start_date, end_date, keywords, False, True  # extended_mode=True
                )
                # Filter by source selection
                filtered_papers = []
                for paper in papers:
                    source = paper.get("source", "")
                    if (source == "biorxiv" and data_sources.get("biorxiv", False)) or (
                        source == "medrxiv" and data_sources.get("medrxiv", False)
                    ):
                        filtered_papers.append(paper)
                return ("biorxiv", filtered_papers)
            except Exception as e:
                return ("biorxiv_error", str(e))
        return ("biorxiv", [])
    
    def fetch_pubmed():
        if data_sources.get("pubmed", False):
            try:
                return (
                    "pubmed",
                    pubmed_fetcher.fetch_papers(
                        start_date, end_date, keywords, False, True  # extended_mode=True
                    ),
                )
            except Exception as e:
                return ("pubmed_error", str(e))
        return ("pubmed", [])
    
    # Execute all API calls in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(fetch_arxiv),
            executor.submit(fetch_biorxiv),
            executor.submit(fetch_pubmed),
        ]
        
        # Collect results
        for future in concurrent.futures.as_completed(futures):
            result_type, result_data = future.result()
            
            if result_type.endswith("_error"):
                source_name = result_type.replace("_error", "")
                st.warning(f"⚠️ Error fetching from {source_name}: {result_data}")
            else:
                all_papers_data.extend(result_data)
    
    if not all_papers_data:
        st.error("❌ No papers found for today!")
        return None
    
    # Step 2: Process and rank papers
    status_text.text("📊 Processing and ranking papers...")
    progress_bar.progress(60)
    
    # Process papers using existing logic
    ranked_papers = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_paper = {
            executor.submit(process_paper_for_kb, paper, keywords): paper for paper in all_papers_data
        }
        
        for future in concurrent.futures.as_completed(future_to_paper):
            try:
                paper_info = future.result()
                if paper_info:
                    ranked_papers.append(paper_info)
            except Exception as e:
                st.warning(f"⚠️ Error processing paper: {e}")
                continue
    
    # Convert to DataFrame and sort by relevance
    df = pd.DataFrame(ranked_papers)
    if not df.empty:
        df = df.sort_values("relevance_score", ascending=False)
        top_papers = df.head(20).to_dict('records')
    else:
        st.error("❌ No papers could be processed!")
        return None
    
    # Step 3: Create knowledge base structure
    status_text.text("💾 Creating knowledge base file...")
    progress_bar.progress(80)
    
    # Create knowledge base structure similar to the existing format
    knowledge_base = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "weeks_covered": 1,
            "keywords_used": keywords,
            "data_sources": {k: v for k, v in data_sources.items() if v},
            "search_mode": search_mode,
            "total_papers": len(top_papers),
            "papers_per_week": 20,
            "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        },
        "weeks": {
            "today": {
                "week_info": {
                    "week_number": 1,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "week_label": f"Today ({start_date.strftime('%Y-%m-%d')})"
                },
                "papers": top_papers,
                "paper_count": len(top_papers)
            }
        }
    }
    
    # Step 4: Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"knowledge_base_today_{timestamp}.json"
    filepath = os.path.join(kb_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, ensure_ascii=False, default=str)
        
        progress_bar.progress(100)
        status_text.text("✅ Knowledge base created successfully!")
        
        st.success(f"🎉 Today's knowledge base created with {len(top_papers)} papers!")
        st.info(f"📁 Saved to: {filepath}")
        
        return filepath
        
    except Exception as e:
        st.error(f"❌ Error saving knowledge base: {e}")
        return None


def create_top_papers_knowledge_base(keywords, data_sources, search_mode="Extended", days_back=7):
    """
    Create a knowledge base with the top 20 most relevant papers currently displayed in the app
    
    Args:
        keywords (list): Keywords to search for
        data_sources (dict): Data sources configuration
        search_mode (str): Search mode (Brief/Standard/Extended)
        days_back (int): Number of days to look back for papers
        
    Returns:
        str: Path to the created knowledge base file
    """
    # Create KB directory if it doesn't exist
    kb_dir = "./KB"
    os.makedirs(kb_dir, exist_ok=True)
    
    st.info("🧠 Creating knowledge base with top 20 most relevant papers...")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Fetch papers using the same logic as the main app
    status_text.text("📚 Fetching papers from all sources...")
    progress_bar.progress(20)
    
    # Use the same fetching logic as the main app
    end_date_normalized = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    papers_df = fetch_and_rank_papers(
        keywords, days_back, data_sources, end_date_normalized, search_mode
    )
    
    if papers_df.empty:
        st.error("❌ No papers found for the specified criteria!")
        return None
    
    # Step 2: Get top 20 papers
    status_text.text("📊 Selecting top 20 most relevant papers...")
    progress_bar.progress(60)
    
    # Filter papers with at least 2 matched keywords (same as main app)
    keyword_filter_mask = papers_df.apply(
        lambda row: len(row.get("matched_keywords", [])) >= 2, axis=1
    )
    filtered_papers = papers_df[keyword_filter_mask]
    
    # Filter papers with relevance score > 4.0 ONLY
    high_relevance_papers = filtered_papers[filtered_papers["relevance_score"] > 4.0]
    
    # Only use papers with relevance score > 4.0
    if len(high_relevance_papers) > 0:
        # Take up to 20 papers, but only those with score > 4.0
        top_papers = high_relevance_papers.head(20).to_dict('records')
        if len(high_relevance_papers) >= 20:
            selection_note = f"Selected top 20 papers, all with relevance score > 4.0"
        else:
            selection_note = f"Selected {len(high_relevance_papers)} papers with relevance score > 4.0 (fewer than 20 available)"
    else:
        # No papers with score > 4.0, don't create KB
        st.warning("❌ No papers found with relevance score > 4.0. Cannot create knowledge base.")
        st.info("💡 Try adjusting your search criteria or date range to find more relevant papers.")
        return None
    
    if not top_papers:
        st.error("❌ No papers meet the minimum keyword requirements!")
        return None
    
    # Step 3: Create knowledge base structure
    status_text.text("💾 Creating knowledge base file...")
    progress_bar.progress(80)
    
    # Get date range for metadata
    start_date = end_date_normalized - timedelta(days=days_back)
    
    # Create knowledge base structure
    knowledge_base = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "weeks_covered": 1,
            "keywords_used": keywords,
            "data_sources": {k: v for k, v in data_sources.items() if v},
            "search_mode": search_mode,
            "days_back": days_back,
            "total_papers_found": len(papers_df),
            "filtered_papers": len(filtered_papers),
            "high_relevance_papers": len(high_relevance_papers),
            "top_papers_selected": len(top_papers),
            "papers_per_week": len(top_papers),
            "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date_normalized.strftime('%Y-%m-%d')}",
            "selection_criteria": "Papers with relevance score > 4.0 ONLY (up to 20 papers)",
            "selection_details": selection_note
        },
        "weeks": {
            "top_papers": {
                "week_info": {
                    "week_number": 1,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date_normalized.isoformat(),
                    "week_label": f"Top 20 Papers ({start_date.strftime('%Y-%m-%d')} to {end_date_normalized.strftime('%Y-%m-%d')})"
                },
                "papers": top_papers,
                "paper_count": len(top_papers)
            }
        }
    }
    
    # Step 4: Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"knowledge_base_top20_{timestamp}.json"
    filepath = os.path.join(kb_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, ensure_ascii=False, default=str)
        
        progress_bar.progress(100)
        status_text.text("✅ Knowledge base created successfully!")
        
        st.success(f"🎉 Knowledge base created with top {len(top_papers)} papers!")
        st.info(f"📁 Saved to: {filepath}")
        st.info(f"📊 Selected from {len(filtered_papers)} filtered papers out of {len(papers_df)} total papers")
        st.info(f"⭐ Selection: {selection_note}")
        
        return filepath
        
    except Exception as e:
        st.error(f"❌ Error saving knowledge base: {e}")
        return None


def process_paper_for_kb(paper, keywords):
    """
    Process a single paper for knowledge base creation
    
    Args:
        paper (dict): Paper data
        keywords (list): Keywords for relevance calculation
        
    Returns:
        dict: Processed paper info or None if processing fails
    """
    try:
        relevance_score, matched_keywords = keyword_matcher.calculate_relevance(
            paper, keywords
        )
        
        # Boost score for target journals (using logic from app.py)
        if paper.get("source") == "PubMed" and paper.get("journal"):
            if is_high_impact_journal(paper["journal"]):
                if len(matched_keywords) >= 5:
                    relevance_score += 5.1
                elif 5 > len(matched_keywords) >= 4:
                    relevance_score += 3.7
                elif 4 > len(matched_keywords) >= 3:
                    relevance_score += 2.8
                elif 3 > len(matched_keywords) >= 2:
                    relevance_score += 1.3
        
        # Format authors list
        authors = paper.get("authors", [])
        if isinstance(authors, list):
            authors_str = ", ".join(authors[:3]) + ("..." if len(authors) > 3 else "")
        else:
            authors_str = str(authors)
        
        # Get source information
        source = paper.get("source", "arXiv")
        if source == "PubMed":
            source_display = "PubMed"
        elif source == "arxiv":
            source_display = "arXiv"
        else:
            source_display = source.capitalize()
        
        paper_info = {
            "title": paper["title"],
            "authors": authors_str,
            "abstract": paper["abstract"],
            "published": paper["published"],
            "arxiv_url": paper.get("arxiv_url", ""),
            "source": source_display,
            "relevance_score": relevance_score,
            "matched_keywords": matched_keywords,
            "journal": paper.get("journal", ""),
            "volume": paper.get("volume", ""),
            "issue": paper.get("issue", ""),
            "pmid": paper.get("pmid", ""),
            "doi": paper.get("doi", ""),
            "categories": paper.get("categories", []),
        }
        
        return paper_info
        
    except Exception as e:
        return None


def display_papers(papers_df):
    """Display papers in a formatted way"""

    for idx, paper in papers_df.iterrows():
        # Check if this is a high-impact journal paper
        is_high_impact = (
            paper.get("source") == "PubMed"
            and paper.get("journal")
            and is_high_impact_journal(paper["journal"])
        )

        # Add spacing between all paper cards
        st.markdown(
            """
            <style>
            div[data-testid="stContainer"][data-border="true"] {
                margin-bottom: 20px !important;
            }
            </style>
        """,
            unsafe_allow_html=True,
        )

        # Style high-impact papers with CSS targeting their container key
        if is_high_impact:
            st.markdown(
                """
                <style>
                [class*="st-key-high-impact-"] {
                    border: 3px solid #B8860B !important;
                    border-radius: 12px !important;
                    background: linear-gradient(135deg,
                        rgba(184, 134, 11, 0.03), rgba(184, 134, 11, 0.08)) !important;
                    box-shadow: 0 4px 8px rgba(184, 134, 11, 0.2) !important;
                }
                </style>
            """,
                unsafe_allow_html=True,
            )
            container_key = f"high-impact-{idx}"
        else:
            container_key = None

        # All papers get a bordered container
        with st.container(border=True, key=container_key):
            # Create columns for layout
            col1, col2 = st.columns([4, 1])

            with col1:
                # Title with link (only if URL exists and is valid)
                title = paper["title"]
                url = paper.get("arxiv_url", "")
                if url and url.startswith(("http://", "https://")):
                    st.markdown(f"### [{title}]({url})")
                else:
                    st.markdown(f"### {title}")
                    if not url:
                        st.caption("⚠️ No URL available")

                # Authors and date
                st.markdown(f"**Authors:** {paper['authors']}")
                st.markdown(f"**Published:** {paper['published']}")

                # Journal information (for PubMed articles)
                if paper.get("source") == "PubMed" and paper.get("journal"):
                    journal_info = paper["journal"]
                    if paper.get("volume") and paper.get("issue"):
                        journal_info += (
                            f", Vol. {paper['volume']}, Issue {paper['issue']}"
                        )
                    elif paper.get("volume"):
                        journal_info += f", Vol. {paper['volume']}"

                    # Check if it's a target journal
                    if is_high_impact_journal(paper["journal"]):
                        st.markdown(f"**Journal:** {journal_info} ⭐")
                        st.markdown(
                            '<div style="color: #B8860B; font-weight: bold; '
                            'font-size: 0.9em;">🌟 Relevant Journal</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"**Journal:** {journal_info}")

                # Abstract (truncated)
                abstract = paper["abstract"]
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
                st.markdown(f"**Abstract:** {abstract}")

                # Matched keywords
                if paper["matched_keywords"]:
                    keywords_str = ", ".join(
                        [f"**{kw}**" for kw in paper["matched_keywords"]]
                    )
                    st.markdown(f"**Matched Keywords:** {keywords_str}")

                # URL for debugging (can be removed later)
                if url:
                    st.caption(f"🔗 Link: {url}")

            with col2:
                # Source badge
                source = paper.get("source", "arXiv")
                source_color = {
                    "arXiv": "#B31B1B",
                    "BioRxiv": "#00A86B",
                    "MedRxiv": "#0066CC",
                    "PubMed": "#FF6B35",
                }.get(source, "#666666")

                st.markdown(
                    f"<div style='text-align: center; margin-bottom: 10px;'>"
                    f"<span style='background-color: {source_color}; "
                    f"color: white; padding: 4px 8px; border-radius: 15px; "
                    f"font-size: 12px; font-weight: bold;'>{source}</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )

                # Relevance score with 4-color quartile-based gradient
                score = paper["relevance_score"]

                # Quartile-based coloring (assuming most scores are 0-10 range)
                # Top 25% (Q4), Upper-middle 25% (Q3), Lower-middle 25% (Q2), Bottom 25% (Q1)
                if score >= 7.5:
                    color = "#00c851"  # Green for top quartile (75th percentile+)
                elif score >= 5:
                    color = "#ffbb33"  # Amber for upper-middle quartile (50-75th)
                elif score >= 2.5:
                    color = "#ff8800"  # Dark Orange for lower-middle quartile (25-50th)
                else:
                    color = "#cc0000"  # Red for bottom quartile (<25th percentile)

                score_display = (
                    f"{score:.1f}" if isinstance(score, int | float) else str(score)
                )
                # Create clickable relevance score that links to paper
                base_style = (
                    "display: flex; flex-direction: column; "
                    "align-items: center; justify-content: center; "
                    f"padding: 10px; border: 2px solid {color}; "
                    "border-radius: 10px; text-align: center;"
                )
                score_div = (
                    f"<div style='color: {color}; font-size: 24px; "
                    f"font-weight: bold; line-height: 1; margin: 0;'>"
                    f"{score_display}</div>"
                )
                label_div = (
                    "<div style='font-size: 12px; margin: 2px 0 0 0; "
                    "color: #666;'>Relevance Score</div>"
                )

                if url and url.startswith(("http://", "https://")):
                    hover_style = (
                        "cursor: pointer; transition: all 0.2s ease;' "
                        "onmouseover='this.style.transform=\"scale(1.05)\"' "
                        "onmouseout='this.style.transform=\"scale(1)\"'"
                    )
                    st.markdown(
                        f"<a href='{url}' target='_blank' "
                        f"style='text-decoration: none;'>"
                        f"<div style='{base_style} {hover_style}>"
                        f"{score_div}{label_div}</div></a>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='{base_style}'>{score_div}{label_div}</div>",
                        unsafe_allow_html=True,
                    )


def render_rag_interface():
    """Render the RAG assistant interface - No API required"""
    st.header("🧠 Research Assistant")
    st.markdown("Search and analyze your research papers with structured summaries and trend analysis!")
    # Minimal card styles for better readability of RAG outputs
    st.markdown(
        """
        <style>
        .rag-card { 
            background: #ffffff; 
            border: 1px solid #eaecf0; 
            border-radius: 12px; 
            padding: 16px 18px; 
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        .rag-card h3 { 
            margin: 0 0 8px 0; 
            font-size: 1rem; 
            color: #1f2937;
            font-weight: 600;
        }
        .rag-card .rag-muted { 
            color: #6b7280; 
            font-size: 0.9rem;
            margin-bottom: 12px;
        }
        .rag-card div {
            color: #374151;
            line-height: 1.5;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Initialize RAG system
    rag_system = initialize_rag_system()
    
    if rag_system is None:
        st.error("❌ RAG system not available")
        return
    
    # Simple Configuration
    with st.expander("⚙️ Configuration", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            top_k = st.slider(
                "Papers to retrieve",
                min_value=3,
                max_value=20,
                value=10,
                help="Number of relevant papers to retrieve for analysis"
            )
            
            force_rebuild = st.checkbox(
                "Force rebuild index",
                help="Rebuild the search index from knowledge base"
            )
        
        with col2:
            if st.button("🚀 Initialize Search System"):
                with st.spinner("Initializing search system..."):
                    success = rag_system.initialize(
                        llm_client_type="local",  # Use local LLM for similarity
                        llm_model="distilbert-base-uncased",  # Better model for similarity
                        force_rebuild=force_rebuild
                    )
                    
                    if success:
                        st.success("✅ Search system initialized successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to initialize search system")
    
    # System Status
    if rag_system.is_initialized:
        with st.expander("📊 System Status", expanded=False):
            status = rag_system.get_system_status()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Papers", status.get("kb_statistics", {}).get("total_papers", 0))
                st.metric("Searchable Docs", status.get("vector_store_statistics", {}).get("total_documents", 0))
            
            with col2:
                sources = status.get("kb_statistics", {}).get("sources", {})
                st.write("**Sources:**")
                for source, count in sources.items():
                    st.write(f"- {source}: {count}")
            
            with col3:
                date_range = status.get("kb_statistics", {}).get("date_range", {})
                st.write("**Date Range:**")
                if date_range:
                    st.write(f"- From: {date_range.get('earliest', 'N/A')}")
                    st.write(f"- To: {date_range.get('latest', 'N/A')}")
                
                # LLM Status
                llm_status = status.get("llm_client", {})
                if llm_status.get("available", False):
                    st.write("**LLM Status:**")
                    st.write(f"- Type: {llm_status.get('type', 'Unknown')}")
                    st.write(f"- Status: 🧠 Semantic similarity enabled")
                else:
                    st.write("**LLM Status:**")
                    st.write(f"- Status: 📊 Jaccard similarity (LLM unavailable)")
    
    # Search Interface
    st.subheader("🔍 Search Research Papers")
    
    # Quick trend analysis buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📅 Tau research trends"):
            st.session_state.rag_query = "tau prediction Alzheimer's disease"
    
    with col2:
        if st.button("🧠 AI in neuroimaging"):
            st.session_state.rag_query = "deep learning machine learning neuroimaging"
    
    with col3:
        if st.button("🔬 Biomarker advances"):
            st.session_state.rag_query = "PET imaging amyloid tau biomarkers"
    
    # Search input
    default_query = st.session_state.get("rag_query", "")
    query = st.text_input(
        "Analyze trends for:",
        value=default_query,
        placeholder="e.g., tau prediction, PET imaging, biomarkers, deep learning"
    )
    
    # Advanced filtering
    with st.expander("🔧 Advanced Filtering"):
        col1, col2 = st.columns(2)
        
        with col1:
            filter_source = st.selectbox(
                "Filter by source",
                ["All", "PubMed", "arXiv", "bioRxiv", "medRxiv"]
            )
            
            filter_journal = st.text_input(
                "Filter by journal (partial match)",
                placeholder="e.g., Nature, Science, JAMA"
            )
        
        with col2:
            weeks_back = st.slider(
                "Papers from last N weeks",
                min_value=1,
                max_value=8,
                value=4
            )
            
            min_relevance = st.slider(
                "Minimum relevance score",
                min_value=0.0,
                max_value=10.0,
                value=0.0,
                step=0.1
            )
    
    # Process search
    if st.button("🔍 Analyze Trends", type="primary") and query.strip():
        if not rag_system.is_initialized:
            st.error("❌ Please initialize the search system first")
            return
        
        with st.spinner("Analyzing research trends..."):
            # Analyze trends for the query
            trend_analysis = rag_system.kb_loader.analyze_trends_for_query(
                query, top_k, 
                llm_client=rag_system.llm_client, 
                vector_store=rag_system.vector_store
            )
            
            if "error" in trend_analysis:
                st.warning(f"❌ {trend_analysis['error']}")
            else:
                # Display trend analysis
                st.subheader(f"📊 Research Trends: '{query}'")
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Matching Papers", trend_analysis['total_matching_papers'])
                
                with col2:
                    st.metric("Analyzed Papers", trend_analysis['analyzed_papers'])
                
                with col3:
                    trends = trend_analysis['trends']
                    avg_relevance = trends.get('relevance_stats', {}).get('avg_relevance', 0)
                    st.metric("Avg Relevance", f"{avg_relevance:.1f}")
                
                with col4:
                    date_range = trends.get('date_range', {})
                    span_days = date_range.get('span_days', 0)
                    st.metric("Time Span", f"{span_days} days")
                
                # Recent vs Historical summaries in side-by-side cards
                comparative_insights = trend_analysis.get('comparative_insights', {})
                left_col, right_col = st.columns(2)
                # Left: Recent Research Summary
                with left_col:
                    recent_summary = comparative_insights.get('recent_papers_summary', '')
                    if recent_summary and "No recent papers found" not in recent_summary:
                        st.markdown(
                            f"""
                            <div class='rag-card'>
                              <h3>📄 Recent Research Summary (Past 7 Days)</h3>
                              <div class='rag-muted'>Auto-generated from most similar recent papers</div>
                              <div>{recent_summary}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.warning("⚠️ No recent papers found for this query in the past 7 days.")
                # Right: Historical Context
                with right_col:
                    hist_summary = comparative_insights.get('historical_context_summary', '')
                    if hist_summary:
                        st.markdown(
                            f"""
                            <div class='rag-card'>
                              <h3>📚 Historical Context (Similar Prior Papers)</h3>
                              <div class='rag-muted'>Context from semantically related earlier work</div>
                              <div>{hist_summary}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                # Comparative Insights
                if comparative_insights and 'insights' in comparative_insights:
                    st.subheader("🔍 Comparative Analysis: This Week vs. Historical Data")
                    
                    insights = comparative_insights['insights']
                    if insights and insights != ["Insufficient data for comparative analysis"]:
                        for insight in insights:
                            st.markdown(f"• {insight}")
                        
                        # Show analysis summary
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"📊 **Analysis Period**: {comparative_insights.get('analysis_period', 'N/A')}")
                        with col2:
                            recent_count = comparative_insights.get('recent_papers_count', 0)
                            historical_count = comparative_insights.get('historical_papers_count', 0)
                            st.info(f"📈 **Data Points**: {recent_count} recent vs {historical_count} historical papers")
                    else:
                        st.warning("⚠️ Insufficient data for comparative analysis. Need more papers in the knowledge base.")
                
                # Research themes
                st.subheader("🎯 Research Themes")
                research_themes = trends.get('research_themes', {})
                if research_themes:
                    theme_cols = st.columns(len(research_themes))
                    for i, (theme, count) in enumerate(research_themes.items()):
                        with theme_cols[i]:
                            st.metric(theme, count)
                
                # Source and journal distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Source Distribution")
                    sources = trends.get('source_distribution', {})
                    for source, count in sources.items():
                        percentage = (count / trend_analysis['analyzed_papers']) * 100
                        st.write(f"**{source}**: {count} papers ({percentage:.1f}%)")
                
                with col2:
                    st.subheader("📚 Top Journals")
                    journals = trends.get('top_journals', {})
                    for journal, count in journals.items():
                        st.write(f"**{journal}**: {count} papers")
                
                # Top keywords
                st.subheader("🏷️ Top Keywords")
                keywords = trends.get('top_keywords', {})
                if keywords:
                    keyword_cols = st.columns(min(5, len(keywords)))
                    for i, (keyword, count) in enumerate(list(keywords.items())[:5]):
                        with keyword_cols[i]:
                            st.metric(keyword, count)
                
                # Date range
                date_range = trends.get('date_range', {})
                if date_range.get('earliest') and date_range.get('latest'):
                    st.subheader("📅 Publication Timeline")
                    st.write(f"**Earliest**: {date_range['earliest']}")
                    st.write(f"**Latest**: {date_range['latest']}")
                    st.write(f"**Span**: {date_range['span_days']} days")
                
                # Top papers
                st.subheader("📄 Top Papers")
                top_papers = trend_analysis.get('top_papers', [])
                
                for i, paper in enumerate(top_papers, 1):
                    with st.expander(f"📄 {i}. {paper['title'][:80]}..."):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Authors:** {paper.get('authors', 'Unknown')}")
                            st.write(f"**Journal:** {paper.get('journal', 'Unknown')}")
                            st.write(f"**Published:** {paper.get('published', 'Unknown')}")
                            st.write(f"**Source:** {paper.get('source', 'Unknown')}")
                            
                            if paper.get('url'):
                                st.write(f"**Link:** [View Paper]({paper['url']})")
                            
                            st.write("**Abstract:**")
                            st.write(paper.get('abstract', 'No abstract available')[:300] + "...")
                        
                        with col2:
                            st.metric("Relevance", f"{paper.get('relevance_score', 0):.1f}")
                            st.metric("Query Match", f"{paper.get('query_match_score', 0)}")
                            
                            if paper.get('matched_keywords'):
                                st.write("**Keywords:**")
                                for keyword in paper['matched_keywords'][:5]:  # Show top 5
                                    st.write(f"- {keyword}")
    
    # Weekly Trend Analysis
    st.subheader("📊 Weekly Research Trends")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        weeks_back = st.slider(
            "Analyze last N weeks",
            min_value=1,
            max_value=4,
            value=1,
            key="trend_weeks"
        )
    
    with col2:
        if st.button("📈 Analyze Trends"):
            if not rag_system.is_initialized:
                st.error("❌ Please initialize the search system first")
            else:
                with st.spinner("Analyzing research trends..."):
                    # Get papers from the specified period
                    from datetime import datetime, timedelta
                    start_date = datetime.now() - timedelta(weeks=weeks_back)
                    end_date = datetime.now()
                    
                    papers = rag_system.kb_loader.get_papers_by_date_range(start_date, end_date)
                    
                    if not papers:
                        st.warning(f"❌ No papers found for the last {weeks_back} week(s)")
                    else:
                        # Sort by relevance
                        papers.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                        top_papers = papers[:20]
                        
                        st.subheader(f"📊 Research Trends - Last {weeks_back} Week(s)")
                        
                        # Source distribution
                        sources = {}
                        journals = {}
                        keywords = {}
                        
                        for paper in top_papers:
                            # Count sources
                            source = paper.get('source', 'Unknown')
                            sources[source] = sources.get(source, 0) + 1
                            
                            # Count journals
                            journal = paper.get('journal', 'Unknown')
                            if journal:
                                journals[journal] = journals.get(journal, 0) + 1
                            
                            # Count keywords
                            for keyword in paper.get('matched_keywords', []):
                                keywords[keyword] = keywords.get(keyword, 0) + 1
                        
                        # Display trends
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write("**📊 Source Distribution:**")
                            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                                st.write(f"- {source}: {count} papers")
                        
                        with col2:
                            st.write("**📚 Top Journals:**")
                            for journal, count in sorted(journals.items(), key=lambda x: x[1], reverse=True)[:5]:
                                st.write(f"- {journal}: {count}")
                        
                        with col3:
                            st.write("**🏷️ Top Keywords:**")
                            for keyword, count in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]:
                                st.write(f"- {keyword}: {count}")
                        
                        # Show top papers
                        st.write(f"**📄 Top {len(top_papers)} Papers:**")
                        for i, paper in enumerate(top_papers[:10], 1):
                            st.write(f"{i}. **{paper['title']}**")
                            st.write(f"   - {paper['authors']} | {paper['journal']} | {paper['published']}")
                            st.write(f"   - Relevance: {paper['relevance_score']:.1f}")
                            st.write("")


if __name__ == "__main__":
    main()
