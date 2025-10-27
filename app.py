import concurrent.futures
import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from components.auth_ui import render_user_menu, require_auth
from config import settings
from fetchers.arxiv_fetcher import ArxivFetcher
from fetchers.biorxiv_fetcher import BioRxivFetcher
from fetchers.pubmed_fetcher import PubMedFetcher
from processors.keyword_matcher import KeywordMatcher
from services.auth_service import AuthService
from services.settings_service import SettingsService
from services.supabase_client import get_supabase_client
from storage.data_storage import DataStorage
from utils.logger import Logger


# Initialize logger
logger = Logger(__name__)


# Set page configuration
st.set_page_config(
    page_title="Manuscript Alert System",
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
        SettingsService(),
    )


@st.cache_resource
def initialize_auth():
    """Initialize authentication service with Supabase client."""
    try:
        supabase_client = get_supabase_client()
        return AuthService(supabase_client)
    except Exception as e:
        logger.error(f"Failed to initialize auth service: {e}")
        st.error("Failed to connect to authentication service. Please check your .env file.")
        st.stop()


(arxiv_fetcher, biorxiv_fetcher, pubmed_fetcher, keyword_matcher, data_storage, settings_service) = (
    initialize_components()
)
auth_service = initialize_auth()

# Load settings from config with caching to prevent excessive disk reads
@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_current_settings():
    logger.debug("Fetching current settings from settings_service")
    settings_dict = settings_service.load_settings()
    logger.debug(f"Retrieved settings with {len(settings_dict.get('keywords', []))} keywords")
    return settings_dict

# Get current keywords from settings
def get_current_keywords():
    settings_dict = get_current_settings()
    return settings_dict.get("keywords", settings.DEFAULT_KEYWORDS)


def main():
    logger.info("=== App started/rerun ===")

    # Require authentication - if not authenticated, show login page and stop
    if not require_auth(auth_service):
        return

    # User is authenticated - show main app
    st.title("Manuscript Alert System")
    st.markdown(
        "Stay updated with the latest Pubmed, arXiv, biorXiv, "
        "and medrXiv papers in your field of interest"
    )

    # Show user menu in sidebar
    render_user_menu(auth_service)

    # Initialize session state for active tab tracking
    if "active_main_tab" not in st.session_state:
        st.session_state.active_main_tab = 0
        logger.debug("Initialized active_main_tab to 0")

    logger.debug(f"Current active_main_tab: {st.session_state.active_main_tab}")

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📚 Papers", "🤖 Models", "⚙️ Settings"])

    with tab1:
        papers_tab()

    with tab2:
        models_tab()

    with tab3:
        settings_tab()


def papers_tab():
    """Main papers tab with search and filtering functionality"""
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")

        # Load user preferences
        preferences = data_storage.load_preferences()

        # Keywords configuration
        st.subheader("Keywords")

        # Load existing keywords or use defaults
        current_keywords = get_current_keywords()

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
            import os

            if os.path.exists("paper_cache.json"):
                os.remove("paper_cache.json")
            st.success("All caches cleared! Data will be refreshed.")
            st.rerun()

        # Date range selection (moved here)
        st.subheader("Date Range")
        days_back = st.slider(
            "Days to look back:",
            min_value=1,
            max_value=21,
            value=7,
            help="Number of days to search back from today",
        )

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

        # Boost score for target journals using settings
        current_settings = get_current_settings()
        journal_scoring = current_settings.get("journal_scoring", {})

        if (paper.get("source") == "PubMed" and paper.get("journal") and
            journal_scoring.get("enabled", True) and is_high_impact_journal(paper["journal"])):

            boosts = journal_scoring.get("high_impact_journal_boost", {})
            num_matches = len(matched_keywords)

            if num_matches >= 5:
                relevance_score += boosts.get("5_or_more_keywords", 5.1)
            elif num_matches >= 4:
                relevance_score += boosts.get("4_keywords", 3.7)
            elif num_matches >= 3:
                relevance_score += boosts.get("3_keywords", 2.8)
            elif num_matches >= 2:
                relevance_score += boosts.get("2_keywords", 1.3)
            elif num_matches >= 1:
                relevance_score += boosts.get("1_keyword", 0.5)

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




def is_journal_excluded(journal_name):
    """Check if a journal should be excluded using pattern matching"""
    if not journal_name:
        return False

    journal_lower = journal_name.lower()

    # Load exclusion patterns from settings
    current_settings = get_current_settings()
    exclusion_patterns = current_settings.get("journal_exclusions", [])

    # Handle both old format (dict) and new format (list)
    if isinstance(exclusion_patterns, list):
        # New simplified format - just check all patterns
        for pattern in exclusion_patterns:
            pattern_lower = pattern.lower()
            if pattern_lower in journal_lower:
                return True
    else:
        # Old format - maintain backward compatibility
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

    # Load target journal patterns from settings
    current_settings = get_current_settings()
    target_patterns = current_settings.get("target_journals", {})

    # Check exact matches first (highest priority)
    for exact_match in target_patterns.get("exact_matches", []):
        if journal_lower == exact_match:
            return True

    # Check family matches (medium priority)
    for family_pattern in target_patterns.get("family_matches", []):
        if journal_lower.startswith(family_pattern):
            return True

    # Check specific journals (lower priority)
    for specific_journal in target_patterns.get("specific_journals", []):
        if specific_journal in journal_lower:
            return True

    return False


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


def settings_tab():
    """Settings tab for configuring keywords, journals, and scoring"""
    logger.info(">>> Entered settings_tab()")

    st.header("⚙️ Application Settings")
    st.markdown("Configure keywords, journal selections, and scoring parameters. Changes are saved to the source code and persist across app runs.")

    # Initialize session state for active settings sub-tab
    if "active_settings_tab" not in st.session_state:
        st.session_state.active_settings_tab = 0
        logger.debug("Initialized active_settings_tab to 0")

    logger.debug(f"Current active_settings_tab: {st.session_state.active_settings_tab}")

    # Load current settings
    logger.info("Loading current settings...")
    current_settings = get_current_settings()
    logger.info(f"Loaded settings with {len(current_settings.get('keywords', []))} keywords")

    # Create tabs within settings
    settings_tab1, settings_tab2, settings_tab3, settings_tab4 = st.tabs([
        "🔍 Keywords", "📰 Journals", "📊 Scoring", "💾 Backup"
    ])

    with settings_tab1:
        logger.debug("Rendering Keywords tab")
        keyword_settings(current_settings)

    with settings_tab2:
        logger.debug("Rendering Journals tab")
        journal_settings(current_settings)

    with settings_tab3:
        logger.debug("Rendering Scoring tab")
        scoring_settings(current_settings)

    with settings_tab4:
        logger.debug("Rendering Backup tab")
        backup_settings()

    logger.info("<<< Exiting settings_tab()")


def keyword_settings(current_settings):
    """Keywords configuration tab"""
    logger.info(">>> Entered keyword_settings()")

    st.subheader("🔍 Research Keywords")
    st.markdown("Configure the keywords used for paper matching. Papers must match at least 2 keywords to be displayed.")

    # Current keywords
    current_keywords = current_settings.get("keywords", [])
    logger.debug(f"Current keywords count: {len(current_keywords)}")

    # Keywords input
    keywords_text = st.text_area(
        "Research Keywords (one per line):",
        value="\n".join(current_keywords),
        height=200,
        help="Enter research topics you're interested in, one per line."
    )

    # Parse keywords
    new_keywords = [k.strip() for k in keywords_text.split("\n") if k.strip()]
    logger.debug(f"Parsed new_keywords count: {len(new_keywords)}")

    # Keyword priority settings
    st.subheader("📈 Keyword Priority Scoring")
    st.markdown("Set priority levels for different keywords to boost their relevance scores.")

    keyword_scoring = current_settings.get("keyword_scoring", {})

    # High priority keywords - filter defaults to only include current keywords
    current_high_priority = [kw for kw in keyword_scoring.get("high_priority", {}).get("keywords", []) if kw in new_keywords]
    logger.debug(f"Current high priority keywords: {current_high_priority}")
    high_priority_keywords = st.multiselect(
        "High Priority Keywords (1.5x boost):",
        options=new_keywords,
        default=current_high_priority,
        help="Keywords that get a 1.5x relevance score boost"
    )

    # Medium priority keywords - filter defaults to only include current keywords
    current_medium_priority = [kw for kw in keyword_scoring.get("medium_priority", {}).get("keywords", []) if kw in new_keywords and kw not in high_priority_keywords]
    logger.debug(f"Current medium priority keywords: {current_medium_priority}")
    medium_priority_keywords = st.multiselect(
        "Medium Priority Keywords (1.2x boost):",
        options=[kw for kw in new_keywords if kw not in high_priority_keywords],
        default=current_medium_priority,
        help="Keywords that get a 1.2x relevance score boost"
    )

    # Show remaining keywords as default priority
    remaining_keywords = [kw for kw in new_keywords if kw not in high_priority_keywords and kw not in medium_priority_keywords]

    if remaining_keywords:
        st.info(f"**Default Priority Keywords (1.0x boost):** {', '.join(remaining_keywords)}")

    # Save keywords
    logger.debug("About to check if Save Keywords button was clicked")
    if st.button("💾 Save Keywords Configuration", type="primary", key="save_keywords_btn"):
        logger.warning("🔴 SAVE KEYWORDS BUTTON CLICKED!")
        logger.info(f"Saving {len(new_keywords)} keywords to settings")
        logger.debug(f"High priority: {high_priority_keywords}")
        logger.debug(f"Medium priority: {medium_priority_keywords}")

        # Update settings
        current_settings["keywords"] = new_keywords
        current_settings["keyword_scoring"] = {
            "high_priority": {
                "keywords": high_priority_keywords,
                "boost": 1.5,
            },
            "medium_priority": {
                "keywords": medium_priority_keywords,
                "boost": 1.2,
            },
        }

        # Save to file
        logger.info("Calling settings_service.save_settings()...")
        save_result = settings_service.save_settings(current_settings)
        logger.info(f"Save result: {save_result}")

        if save_result:
            st.success("✅ Keywords configuration saved successfully!")
            logger.warning("🔄 About to call st.rerun()")
            get_current_settings.clear()  # Clear cache before rerun
            st.rerun()
        else:
            st.error("❌ Failed to save keywords configuration.")
            logger.error("Failed to save keywords configuration")

    logger.info("<<< Exiting keyword_settings()")


def journal_settings(current_settings):
    """Journal configuration tab"""
    st.subheader("📰 Journal Selection & Filtering")

    # Target journals
    st.markdown("### Target Journals")
    st.markdown("Configure which journals are considered high-impact and get scoring boosts.")

    target_journals = current_settings.get("target_journals", {})

    # Exact matches
    exact_matches = st.text_area(
        "Exact Journal Matches (highest priority):",
        value="\n".join(target_journals.get("exact_matches", [])),
        height=100,
        help="Journal names that must match exactly (case-insensitive)"
    )

    # Family matches
    family_matches = st.text_area(
        "Journal Family Matches (medium priority):",
        value="\n".join(target_journals.get("family_matches", [])),
        height=100,
        help="Journal name prefixes (e.g., 'nature ' for all Nature journals)"
    )

    # Specific journals
    specific_journals = st.text_area(
        "Specific Journal Names (lower priority):",
        value="\n".join(target_journals.get("specific_journals", [])),
        height=150,
        help="Full journal names or partial matches"
    )

    # Journal exclusions
    st.markdown("### Journal Exclusions")
    st.markdown("Configure patterns to exclude from target journal matching. Enter one exclusion pattern per line.")
    st.markdown("*Any journal containing these patterns will be excluded from high-impact journal scoring.*")

    journal_exclusions = current_settings.get("journal_exclusions", {})

    # Collect current exclusions - handle both old format (dict) and new format (list)
    if isinstance(journal_exclusions, list):
        all_exclusions = journal_exclusions
    else:
        # Old format - collect from all categories
        all_exclusions = []
        if journal_exclusions.get("radiology_exclusions"):
            all_exclusions.extend(journal_exclusions["radiology_exclusions"])
        if journal_exclusions.get("brain_exclusions"):
            all_exclusions.extend(journal_exclusions["brain_exclusions"])
        if journal_exclusions.get("neuroscience_exclusions"):
            all_exclusions.extend(journal_exclusions["neuroscience_exclusions"])
        if journal_exclusions.get("other_exclusions"):
            all_exclusions.extend(journal_exclusions["other_exclusions"])

    exclusion_patterns = st.text_area(
        "Journal Exclusion Patterns:",
        value="\n".join(all_exclusions),
        height=200,
        help="Enter patterns to exclude (e.g., 'pediatric', 'abdominal', 'case reports'). Any journal containing these patterns will be excluded from target journal scoring."
    )

    # Parse exclusion patterns into a single list
    exclusion_list = [pattern.strip() for pattern in exclusion_patterns.split("\n") if pattern.strip()]

    # Show current exclusions
    if exclusion_list:
        st.markdown("**Current Exclusion Patterns:**")
        for pattern in exclusion_list:
            st.write(f"• {pattern}")

    # Save journal settings
    logger.debug("About to check if Save Journal Configuration button was clicked")
    if st.button("💾 Save Journal Configuration", type="primary", key="save_journal_btn"):
        logger.warning("🔴 SAVE JOURNAL BUTTON CLICKED!")
        logger.info(f"Saving journal configuration with {len(exclusion_list)} exclusions")

        # Update settings
        current_settings["target_journals"] = {
            "exact_matches": [j.strip() for j in exact_matches.split("\n") if j.strip()],
            "family_matches": [j.strip() for j in family_matches.split("\n") if j.strip()],
            "specific_journals": [j.strip() for j in specific_journals.split("\n") if j.strip()],
        }

        # Simplified: all exclusions apply to all journal types
        current_settings["journal_exclusions"] = exclusion_list

        # Save to file
        logger.info("Calling settings_service.save_settings()...")
        save_result = settings_service.save_settings(current_settings)
        logger.info(f"Save result: {save_result}")

        if save_result:
            st.success("✅ Journal configuration saved successfully!")
            logger.warning("🔄 About to call st.rerun()")
            get_current_settings.clear()  # Clear cache before rerun
            st.rerun()
        else:
            st.error("❌ Failed to save journal configuration.")
            logger.error("Failed to save journal configuration")


def scoring_settings(current_settings):
    """Scoring configuration tab"""
    st.subheader("📊 Relevance Scoring Configuration")

    # Journal scoring
    st.markdown("### Journal Impact Scoring")
    journal_scoring = current_settings.get("journal_scoring", {})

    scoring_enabled = st.checkbox(
        "Enable Journal Impact Scoring",
        value=journal_scoring.get("enabled", True),
        help="Whether to apply scoring boosts for high-impact journals"
    )

    if scoring_enabled:
        st.markdown("**High-Impact Journal Score Boosts (based on keyword matches):**")

        boosts = journal_scoring.get("high_impact_journal_boost", {})

        col1, col2 = st.columns(2)

        with col1:
            boost_5_or_more = st.number_input(
                "5+ keywords matched:",
                value=boosts.get("5_or_more_keywords", 5.1),
                step=0.1,
                format="%.1f"
            )

            boost_4 = st.number_input(
                "4 keywords matched:",
                value=boosts.get("4_keywords", 3.7),
                step=0.1,
                format="%.1f"
            )

        with col2:
            boost_3 = st.number_input(
                "3 keywords matched:",
                value=boosts.get("3_keywords", 2.8),
                step=0.1,
                format="%.1f"
            )

            boost_2 = st.number_input(
                "2 keywords matched:",
                value=boosts.get("2_keywords", 1.3),
                step=0.1,
                format="%.1f"
            )

            boost_1 = st.number_input(
                "1 keyword matched:",
                value=boosts.get("1_keyword", 0.5),
                step=0.1,
                format="%.1f"
            )

    # Search settings
    st.markdown("### Search Configuration")
    search_settings = current_settings.get("search_settings", {})

    col1, col2 = st.columns(2)

    with col1:
        default_days_back = st.number_input(
            "Default Days Back:",
            value=search_settings.get("days_back", 7),
            min_value=1,
            max_value=30
        )

        min_keyword_matches = st.number_input(
            "Minimum Keyword Matches:",
            value=search_settings.get("min_keyword_matches", 2),
            min_value=1,
            max_value=10
        )

    with col2:
        search_mode = st.selectbox(
            "Default Search Mode:",
            options=["Brief", "Standard", "Extended"],
            index=["Brief", "Standard", "Extended"].index(search_settings.get("search_mode", "Brief"))
        )

        max_results = st.number_input(
            "Maximum Results Display:",
            value=search_settings.get("max_results_display", 50),
            min_value=10,
            max_value=200
        )

    # Default data sources
    st.markdown("### Default Data Sources")
    default_sources = search_settings.get("default_sources", {})

    col1, col2 = st.columns(2)

    with col1:
        use_pubmed = st.checkbox("PubMed", value=default_sources.get("pubmed", True))
        use_arxiv = st.checkbox("arXiv", value=default_sources.get("arxiv", False))

    with col2:
        use_biorxiv = st.checkbox("bioRxiv", value=default_sources.get("biorxiv", False))
        use_medrxiv = st.checkbox("medRxiv", value=default_sources.get("medrxiv", False))

    # Save scoring settings
    logger.debug("About to check if Save Scoring Configuration button was clicked")
    if st.button("💾 Save Scoring Configuration", type="primary", key="save_scoring_btn"):
        logger.warning("🔴 SAVE SCORING BUTTON CLICKED!")
        logger.info(f"Saving scoring configuration (enabled: {scoring_enabled})")

        # Update settings
        if scoring_enabled:
            current_settings["journal_scoring"] = {
                "enabled": True,
                "high_impact_journal_boost": {
                    "5_or_more_keywords": boost_5_or_more,
                    "4_keywords": boost_4,
                    "3_keywords": boost_3,
                    "2_keywords": boost_2,
                    "1_keyword": boost_1,
                }
            }
        else:
            current_settings["journal_scoring"] = {"enabled": False}

        current_settings["search_settings"] = {
            "days_back": default_days_back,
            "search_mode": search_mode,
            "min_keyword_matches": min_keyword_matches,
            "max_results_display": max_results,
            "default_sources": {
                "pubmed": use_pubmed,
                "arxiv": use_arxiv,
                "biorxiv": use_biorxiv,
                "medrxiv": use_medrxiv,
            },
            "journal_quality_filter": search_settings.get("journal_quality_filter", False),
        }

        # Save to file
        logger.info("Calling settings_service.save_settings()...")
        save_result = settings_service.save_settings(current_settings)
        logger.info(f"Save result: {save_result}")

        if save_result:
            st.success("✅ Scoring configuration saved successfully!")
            logger.warning("🔄 About to call st.rerun()")
            get_current_settings.clear()  # Clear cache before rerun
            st.rerun()
        else:
            st.error("❌ Failed to save scoring configuration.")
            logger.error("Failed to save scoring configuration")


def models_tab():
    """Models tab for saving and loading different settings presets"""
    st.header("🤖 Model Management")
    st.markdown("Save and manage different configuration presets for different research scenarios. Switch between different research setups with one click.")

    # Load current settings
    current_settings = get_current_settings()

    # Create models directory if it doesn't exist
    models_dir = "config/models"
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    # Save current settings as a new model
    st.markdown("### Save Current Settings as Model")

    col1, col2 = st.columns([2, 1])

    with col1:
        model_name = st.text_input(
            "Model Name:",
            placeholder="e.g., 'AD Neuroimaging Focus', 'General Neuroscience'",
            help="Enter a descriptive name for this configuration preset"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        save_button = st.button("💾 Save Model", type="primary")

    if save_button and model_name.strip():
        model_name_clean = "".join(c for c in model_name if c.isalnum() or c in (" ", "-", "_")).rstrip()
        if model_name_clean:
            model_file = os.path.join(models_dir, f"{model_name_clean.replace(' ', '_')}.json")

            try:
                import json
                with open(model_file, "w", encoding="utf-8") as f:
                    json.dump(current_settings, f, indent=2, ensure_ascii=False)
                st.success(f"✅ Model '{model_name_clean}' saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error saving model: {e}")
        else:
            st.error("❌ Please enter a valid model name (alphanumeric characters, spaces, hyphens, underscores only)")
    elif save_button and not model_name.strip():
        st.error("❌ Please enter a model name")

    # List existing models
    st.markdown("### Load Existing Models")

    # Get list of model files
    model_files = []
    if os.path.exists(models_dir):
        for file in os.listdir(models_dir):
            if file.endswith(".json"):
                model_files.append(file)

    if model_files:
        st.markdown(f"Found {len(model_files)} saved models:")

        for i, model_file in enumerate(sorted(model_files)):
            model_name = model_file.replace(".json", "").replace("_", " ")
            model_path = os.path.join(models_dir, model_file)

            # Get file modification time
            mod_time = os.path.getmtime(model_path)
            mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.write(f"**{model_name}**")
                st.caption(f"Last modified: {mod_time_str}")

            with col2:
                if st.button("Load", key=f"model_load_{i}"):
                    try:
                        import json
                        with open(model_path, encoding="utf-8") as f:
                            loaded_settings = json.load(f)

                        # Save the loaded settings as current settings
                        if settings_service.save_settings(loaded_settings):
                            st.success(f"✅ Model '{model_name}' loaded successfully!")
                            get_current_settings.clear()  # Clear cache before rerun
                            st.rerun()
                        else:
                            st.error("❌ Error applying model settings")
                    except Exception as e:
                        st.error(f"❌ Error loading model: {e}")

            with col3:
                if st.button("Preview", key=f"model_preview_{i}"):
                    try:
                        import json
                        with open(model_path, encoding="utf-8") as f:
                            loaded_settings = json.load(f)

                        # Show preview in expander
                        with st.expander(f"Preview: {model_name}", expanded=True):
                            st.write("**Keywords:**")
                            keywords = loaded_settings.get("keywords", [])
                            st.write(f"{len(keywords)} keywords: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")

                            st.write("**Journal Exclusions:**")
                            exclusions = loaded_settings.get("journal_exclusions", [])
                            st.write(f"{len(exclusions)} exclusion patterns")

                            st.write("**Target Journals:**")
                            target_journals = loaded_settings.get("target_journals", {})
                            exact_matches = target_journals.get("exact_matches", [])
                            st.write(f"Exact matches: {', '.join(exact_matches[:3])}{'...' if len(exact_matches) > 3 else ''}")

                            st.write("**Search Settings:**")
                            search_settings = loaded_settings.get("search_settings", {})
                            st.write(f"Days back: {search_settings.get('days_back', 'N/A')}")
                            st.write(f"Search mode: {search_settings.get('search_mode', 'N/A')}")

                    except Exception as e:
                        st.error(f"❌ Error previewing model: {e}")

            with col4:
                if st.button("Delete", key=f"model_delete_{i}"):
                    try:
                        os.remove(model_path)
                        st.success(f"✅ Model '{model_name}' deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error deleting model: {e}")

            st.markdown("---")
    else:
        st.info("No saved models found. Save your current settings as a model to get started!")

    # Quick actions
    st.markdown("### Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📋 Export Current Settings"):
            try:
                import json
                settings_json = json.dumps(current_settings, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 Download Settings JSON",
                    data=settings_json,
                    file_name=f"manuscript_alert_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )
            except Exception as e:
                st.error(f"❌ Error exporting settings: {e}")

    with col2:
        uploaded_file = st.file_uploader("📤 Import Settings", type=["json"], help="Upload a JSON settings file to import")
        if uploaded_file is not None:
            try:
                import json
                imported_settings = json.load(uploaded_file)

                if st.button("Import Settings"):
                    if settings_service.save_settings(imported_settings):
                        st.success("✅ Settings imported successfully!")
                        get_current_settings.clear()  # Clear cache before rerun
                        st.rerun()
                    else:
                        st.error("❌ Error importing settings")
            except Exception as e:
                st.error(f"❌ Error importing settings: {e}")


def backup_settings():
    """Backup and restore settings"""
    st.subheader("💾 Settings Backup & Restore")

    # List available backups
    backups = settings_service.list_backups()

    if backups:
        st.markdown("### Available Backups")

        for i, backup_file in enumerate(backups[:10]):  # Show last 10 backups
            backup_name = os.path.basename(backup_file)
            backup_date = backup_name.replace("settings_backup_", "").replace(".py", "")

            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.text(f"Backup {i+1}: {backup_date}")

            with col2:
                if st.button("Restore", key=f"backup_restore_{i}"):
                    if settings_service.restore_backup(backup_file):
                        st.success("✅ Backup restored successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to restore backup.")

            with col3:
                if st.button("Delete", key=f"backup_delete_{i}"):
                    try:
                        os.remove(backup_file)
                        st.success("✅ Backup deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to delete backup: {e}")
    else:
        st.info("No backup files found. Backups are automatically created when you save settings.")

    # Manual backup creation
    st.markdown("### Create Manual Backup")
    if st.button("📁 Create Backup Now"):
        # Load current settings and save them (this will create a backup)
        current_settings = get_current_settings()
        if settings_service.save_settings(current_settings):
            st.success("✅ Manual backup created successfully!")
        else:
            st.error("❌ Failed to create backup.")


if __name__ == "__main__":
    main()
