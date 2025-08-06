import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import concurrent.futures
from arxiv_fetcher import ArxivFetcher
from biorxiv_fetcher import BioRxivFetcher
from pubmed_fetcher import PubMedFetcher
from keyword_matcher import KeywordMatcher
from data_storage import DataStorage

# Set page configuration
st.set_page_config(
    page_title="Manuscript Alert System for AD and Neuroimaging",
    #page_icon="📚",
    layout="wide")


# Initialize components
@st.cache_resource
def initialize_components():
    return ArxivFetcher(), BioRxivFetcher(), PubMedFetcher(), KeywordMatcher(
    ), DataStorage()


arxiv_fetcher, biorxiv_fetcher, pubmed_fetcher, keyword_matcher, data_storage = initialize_components(
)

# Default keywords
DEFAULT_KEYWORDS = [
    "Alzheimer's disease", "PET", "MRI", "dementia", "amyloid", "tau",
    "plasma", "brain"
]


def main():
    st.title("Manuscript Alert System for AD and Neuroimaging")
    st.markdown(
        "Stay updated with the latest Pubmed, arXiv, biorXiv, and medrXiv papers in Donghoon's field of interest"
    )

    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")

        # Load user preferences
        preferences = data_storage.load_preferences()

        # Keywords configuration
        st.subheader("Keywords")

        # Load existing keywords or use defaults
        current_keywords = preferences.get('keywords', DEFAULT_KEYWORDS)

        # Text area for keywords input
        keywords_text = st.text_area(
            "Enter keywords (one per line):",
            value="\n".join(current_keywords),
            height=150,
            help=
            "Enter research topics you're interested in, one per line. Papers must match at least 2 keywords to be displayed."
        )

        # Parse keywords from text area
        keywords = [k.strip() for k in keywords_text.split('\n') if k.strip()]

        # Save preferences button
        if st.button("💾 Save Keywords"):
            preferences['keywords'] = keywords
            data_storage.save_preferences(preferences)
            st.success("Keywords saved!")
            st.rerun()

        # Journal Quality Filter
        st.subheader("Journal Quality")
        show_high_impact_only = st.checkbox(
            "🌟 Relevant Journals Only",
            value=False,
            help=
            "Show only papers from: Nature/JAMA/NPJ/Science journals, Radiology, AJNR, Brain, MRM, JMRI, and Alzheimer's & Dementia"
        )

        # Search limit selection
        st.subheader("Search Limits")
        search_mode = st.radio(
            "Article search limit:", [
                "Brief (PubMed: 1000, Others: 500)",
                "Standard (PubMed: 2500, Others: 1000)",
                "Extended (All sources: 5000)"
            ],
            index=0,
            help="Choose search depth vs speed trade-off")

        if search_mode.startswith("Extended"):
            st.caption(
                "⚠️ Extended mode may take 2-3x longer but provides comprehensive results."
            )
        elif search_mode.startswith("Standard"):
            st.caption(
                "⚠️ Standard mode balanced for speed and coverage."
            )
        else:
            st.caption(
                "⚠️ Brief mode optimized for fastest results with recent papers."
            )

        # Data sources selection
        st.subheader("Data Sources")
        col1, col2 = st.columns(2)

        with col1:
            use_arxiv = st.checkbox("arXiv",
                                    value=False,
                                    help="Include papers from arXiv")
            use_biorxiv = st.checkbox("bioRxiv",
                                      value=False,
                                      help="Include papers from bioRxiv")
        with col2:
            use_medrxiv = st.checkbox("medRxiv",
                                      value=False,
                                      help="Include papers from medRxiv")
            use_pubmed = st.checkbox("PubMed",
                                     value=True,
                                     help="Include papers from PubMed")

        # Refresh data
        st.subheader("Data Management")
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            # Also clear any file-based cache
            import os
            if os.path.exists('paper_cache.json'):
                os.remove('paper_cache.json')
            st.success("All caches cleared! Data will be refreshed.")
            st.rerun()

        # Date range selection (moved here)
        st.subheader("Date Range")
        days_back = st.slider("Days to look back:",
                              min_value=1,
                              max_value=21,
                              value=7,
                              help="Number of days to search back from today")

    # Main content area
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("Recent Papers")

        # Display current keywords
        if keywords:
            st.info(f"**Active Keywords:** {', '.join(keywords[:5])}" +
                    (f" and {len(keywords)-5} more..." if len(keywords) >
                     5 else ""))
        else:
            st.warning(
                "No keywords configured. Please add some keywords in the sidebar."
            )
            return

        # Create data sources dict
        data_sources = {
            'arxiv': use_arxiv,
            'biorxiv': use_biorxiv,
            'medrxiv': use_medrxiv,
            'pubmed': use_pubmed
        }

        # Check if at least one source is selected
        if not any(data_sources.values()):
            st.warning(
                "Please select at least one data source in the sidebar.")
            return

        # Fetch and process papers
        source_names = [k for k, v in data_sources.items() if v]
        with st.spinner(f"Fetching papers from {', '.join(source_names)}..."):
            # Normalize end_date to current day to make cache more predictable
            end_date_normalized = datetime.now().replace(hour=0,
                                                         minute=0,
                                                         second=0,
                                                         microsecond=0)
            papers = fetch_and_rank_papers(keywords, days_back, data_sources,
                                           end_date_normalized, search_mode)

        if papers.empty:
            st.warning(
                "No papers found for the specified keywords and date range.")
            return

        # Search within results
        search_query = st.text_input("🔍 Search within results:",
                                     placeholder="Enter search term...")

        # Apply filters
        filtered_papers = papers.copy()

        # Search filter
        if search_query:
            filtered_papers = filtered_papers[
                filtered_papers['title'].str.
                contains(search_query, case=False, na=False)
                | filtered_papers['abstract'].str.
                contains(search_query, case=False, na=False)
                | filtered_papers['authors'].str.
                contains(search_query, case=False, na=False)]

        # Relevant journal filter
        if show_high_impact_only:
            high_impact_mask = filtered_papers.apply(
                lambda row: (row.get('source') == 'PubMed' and row.get(
                    'journal') and is_high_impact_journal(row['journal'])),
                axis=1)
            filtered_papers = filtered_papers[high_impact_mask]

        # Filter papers with at least 2 matched keywords
        keyword_filter_mask = filtered_papers.apply(
            lambda row: len(row.get('matched_keywords', [])) >= 2, axis=1)
        filtered_papers = filtered_papers[keyword_filter_mask]

        # Display results count
        st.markdown(
            f"**Found {len(filtered_papers)} papers** (showing top {min(len(filtered_papers), 50)})"
        )

        if len(filtered_papers) < len(papers):
            excluded_count = len(papers) - len(filtered_papers)
            st.caption(
                f"Note: {excluded_count} papers excluded (require minimum 2 matched keywords)"
            )

        # Warning for large date ranges
        if days_back > 14:
            total_fetched = len(papers)
            if total_fetched >= 5000:  # Close to extended API limits
                st.warning(
                    f"⚠️ Large date range ({days_back} days) may hit API limits. Consider reducing the date range or using more specific keywords if you suspect missing papers."
                )

        # Display papers
        display_papers(filtered_papers.head(50))

    with col2:
        st.header("📊 Statistics")

        if not papers.empty:
            # Summary statistics
            st.metric("Total Papers", len(papers))
            try:
                avg_score = float(papers['relevance_score'].mean())
                max_score = float(papers['relevance_score'].max())
                st.metric("Avg Relevance Score", f"{avg_score:.1f}")
                st.metric("Max Relevance Score", f"{max_score:.0f}")
            except Exception:
                st.metric("Avg Relevance Score", "N/A")
                st.metric("Max Relevance Score", "N/A")

            # Source distribution
            st.subheader("📊 Sources")
            source_counts = papers['source'].value_counts()
            for source, count in source_counts.items():
                st.write(f"• **{source}**: {count}")

            # Target journals count
            high_impact_count = 0

            for _, paper in papers.iterrows():
                if paper.get('source') == 'PubMed' and paper.get('journal'):
                    journal_name = paper['journal']
                    if is_high_impact_journal(journal_name):
                        high_impact_count += 1

            if high_impact_count > 0:
                st.subheader("🏆 Journal Quality")
                st.metric("Relevant Journals", high_impact_count)
                st.caption(
                    "Papers from Nature/JAMA/NPJ/Science journals, Radiology, AJNR, Brain, MRM, JMRI, and Alzheimer's & Dementia"
                )

            # Top keywords found
            st.subheader("Top Keywords Found")
            keyword_counts = {}
            for _, paper in papers.iterrows():
                for kw in paper['matched_keywords']:
                    keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

            if keyword_counts:
                top_keywords = sorted(keyword_counts.items(),
                                      key=lambda x: x[1],
                                      reverse=True)[:10]
                for kw, count in top_keywords:
                    st.write(f"• **{kw}**: {count}")

            # Debug: Show unique journals found
            if st.checkbox("🔍 Show Journal Debug Info", value=False):
                st.subheader("All Journals Found")
                all_journals = set()
                target_journals_found = set()

                for _, paper in papers.iterrows():
                    if paper.get('source') == 'PubMed' and paper.get(
                            'journal'):
                        journal = paper['journal'].lower()
                        all_journals.add(journal)
                        if is_high_impact_journal(paper['journal']):
                            target_journals_found.add(journal)

                st.write("**Target Journals Found:**")
                for journal in sorted(target_journals_found):
                    st.write(f"• {journal}")

                st.write("**All Journals (first 20):**")
                for journal in sorted(list(all_journals))[:20]:
                    st.write(f"• {journal}")

            # Export functionality
            st.subheader("📥 Export")
            if st.button("Download Results as CSV"):
                csv = papers.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=
                    f"arxiv_papers_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv")


@st.cache_data(ttl=600)  # Cache for 10 minutes for faster updates
def fetch_and_rank_papers(keywords,
                          days_back,
                          data_sources,
                          end_date=None,
                          search_mode="Standard"):
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
        if data_sources.get('arxiv', False):
            try:
                return ('arxiv',
                        arxiv_fetcher.fetch_papers(start_date, end_date,
                                                   keywords, brief_mode, extended_mode))
            except Exception as e:
                return ('arxiv_error', str(e))
        return ('arxiv', [])

    def fetch_biorxiv():
        if data_sources.get('biorxiv', False) or data_sources.get(
                'medrxiv', False):
            try:
                biorxiv_papers = biorxiv_fetcher.fetch_papers(
                    start_date, end_date, keywords, brief_mode, extended_mode)
                # Filter by source selection
                filtered_papers = []
                for paper in biorxiv_papers:
                    source = paper.get('source', '')
                    if (source == 'biorxiv' and data_sources.get('biorxiv', False)) or \
                       (source == 'medrxiv' and data_sources.get('medrxiv', False)):
                        filtered_papers.append(paper)
                return ('biorxiv', filtered_papers)
            except Exception as e:
                return ('biorxiv_error', str(e))
        return ('biorxiv', [])

    def fetch_pubmed():
        if data_sources.get('pubmed', False):
            try:
                return ('pubmed',
                        pubmed_fetcher.fetch_papers(start_date, end_date,
                                                    keywords, brief_mode, extended_mode))
            except Exception as e:
                return ('pubmed_error', str(e))
        return ('pubmed', [])

    # Execute all API calls in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(fetch_arxiv),
            executor.submit(fetch_biorxiv),
            executor.submit(fetch_pubmed)
        ]

        # Collect results
        for future in concurrent.futures.as_completed(futures):
            result_type, result_data = future.result()

            if result_type.endswith('_error'):
                source_name = result_type.replace('_error', '')
                st.error(f"Error fetching from {source_name}: {result_data}")
            else:
                all_papers_data.extend(result_data)

    if not all_papers_data:
        return pd.DataFrame()

    # Define processing function for parallel execution
    def process_paper(paper):
        relevance_score, matched_keywords = keyword_matcher.calculate_relevance(
            paper, keywords)

        # Boost score for target journals (only if at least 2 keywords matched)
        if paper.get('source') == 'PubMed' and paper.get('journal'):
            # if is_high_impact_journal(
            #         paper['journal']) and len(matched_keywords) >= 2:
            #     relevance_score += 3.0  # Boost target journal papers with sufficient keyword matches
            if is_high_impact_journal(paper['journal']):
                if len(matched_keywords) >= 5:
                    relevance_score += 4.1
                elif 5 > len(matched_keywords) >= 4:
                    relevance_score += 3.4
                elif 4 > len(matched_keywords) >= 3:
                    relevance_score += 2.8
                elif 3 > len(matched_keywords) >= 2:
                    relevance_score += 1.3

        # Format authors list
        authors = paper.get('authors', [])
        if isinstance(authors, list):
            authors_str = ', '.join(
                authors[:3]) + ('...' if len(authors) > 3 else '')
        else:
            authors_str = str(authors)

        return (paper, relevance_score, matched_keywords, authors_str)

    # Process papers in parallel for faster ranking
    ranked_papers = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_paper = {
            executor.submit(process_paper, paper): paper
            for paper in all_papers_data
        }

        for future in concurrent.futures.as_completed(future_to_paper):
            try:
                paper, relevance_score, matched_keywords, authors_str = future.result(
                )

                # Get source information
                source = paper.get('source', 'arXiv')
                if source == 'PubMed':
                    source_display = 'PubMed'
                elif source == 'arxiv':
                    source_display = 'arXiv'
                else:
                    source_display = source.capitalize()

                paper_info = {
                    'title': paper['title'],
                    'authors': authors_str,
                    'abstract': paper['abstract'],
                    'published': paper['published'],
                    'arxiv_url': paper.get('arxiv_url', ''),
                    'source': source_display,
                    'relevance_score': relevance_score,
                    'matched_keywords': matched_keywords,
                    'journal': paper.get('journal', ''),
                    'volume': paper.get('volume', ''),
                    'issue': paper.get('issue', '')
                }

                ranked_papers.append(paper_info)
            except Exception as e:
                continue  # Skip papers that fail processing

    # Convert to DataFrame efficiently and sort by relevance
    df = pd.DataFrame(ranked_papers)
    df = df.sort_values('relevance_score', ascending=False)

    return df


def get_exclusion_patterns():
    """Get patterns for excluding journals from target journal matching"""
    return {
        # Radiology subspecialties - exclude if they contain these specific patterns
        'radiology_exclusions': [
            'abdominal radiology',
            'pediatric radiology',
            'cardiovascular and interventional radiology',
            'interventional radiology',
            'emergency radiology',
            'skeletal radiology',
            'clinical radiology',
            'academic radiology',
            'investigative radiology',
            'case reports',  # This will exclude "radiology case reports"
            'oral surgery',  # This will exclude the long oral surgery journal name
            'korean journal of radiology',
            'the neuroradiology journal',
            'interventional neuroradiology',
            'japanese journal of radiology',
        ],
        # Brain subspecialties - exclude these specific patterns
        'brain_exclusions': [
            'brain research',  # Exclude if exact match
            'brain and behavior',
            'brain imaging and behavior',
            'brain stimulation',
            'brain connectivity',
            'brain and cognition',
            'brain, behavior, and immunity',
            'metabolic brain disease',
        ],
        # Neuroscience subspecialties - exclude these patterns
        'neuroscience_exclusions': [
            'neuroscience letters',
            'neuroscience bulletin',
            'neuroscience methods',
            'neuroscience research',
            'neuroscience and biobehavioral',
            'clinical neuroscience',
            'neuropsychiatry',
            'ibro neuroscience',
            'acs chemical neuroscience',
        ],
        # Other exclusions
        'other_exclusions': [
            'proceedings of the national academy',
            'life science alliance',
            'life sciences',
            'animal science',
            'biomaterials science',
            'veterinary medical science',
            'philosophical transactions',
            'annals of the new york academy',
        ]
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
            if category == 'radiology_exclusions':
                if 'radiology' in journal_lower and pattern_lower in journal_lower:
                    # Exception: don't exclude plain "radiology"
                    if journal_lower.strip() == 'radiology':
                        continue
                    return True

            # For brain, be more specific
            elif category == 'brain_exclusions':
                if 'brain' in journal_lower and pattern_lower in journal_lower:
                    # Exception: don't exclude plain "brain"
                    if journal_lower.strip() == 'brain':
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
        'exact_matches': [
            'jama',
            'nature',
            'science',
            #'brain',
            'radiology',
            'ajnr',
            'the lancet',
        ],
        # Medium priority - specific journal families
        'family_matches': [
            'jama ',  # Space ensures it's part of JAMA family
            'nature ',  # Space ensures it's part of Nature family
            'science ',  # Space ensures it's part of Science family
            'npj ',  # Nature Partner Journals
            'the lancet',
            
        ],
        # Specific important journals
        'specific_journals': [
            'american journal of neuroradiology',
            'alzheimer\'s & dementia',
            'alzheimers dement',
            'ebiomedicine',
            'journal of magnetic resonance imaging',
            'magnetic resonance in medicine',
            'radiology',
            'jmri',
            'j magn reson imaging',
            #'brain',
            'brain : a journal of neurology',
        ]
    }

    # Check exact matches first (highest priority)
    for exact_match in target_patterns['exact_matches']:
        if journal_lower == exact_match:
            return True

    # Check family matches (medium priority)
    for family_pattern in target_patterns['family_matches']:
        if journal_lower.startswith(family_pattern):
            return True

    # Check specific journals (lower priority)
    for specific_journal in target_patterns['specific_journals']:
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


def display_papers(papers_df):
    """Display papers in a formatted way"""

    for idx, paper in papers_df.iterrows():
        # Check if this is a high-impact journal paper
        is_high_impact = (paper.get('source') == 'PubMed'
                          and paper.get('journal')
                          and is_high_impact_journal(paper['journal']))

        # Add special styling for high-impact papers
        if is_high_impact:
            st.markdown(
                '<div style="border: 2px solid #FFD700; border-radius: 10px; padding: 15px; background-color: rgba(255, 215, 0, 0.1); margin-bottom: 20px;">',
                unsafe_allow_html=True)

        with st.container():
            # Create columns for layout
            col1, col2 = st.columns([4, 1])

            with col1:
                # Title with link (only if URL exists and is valid)
                title = paper['title']
                url = paper.get('arxiv_url', '')
                if url and url.startswith(('http://', 'https://')):
                    st.markdown(f"### [{title}]({url})")
                else:
                    st.markdown(f"### {title}")
                    if not url:
                        st.caption("⚠️ No URL available")

                # Authors and date
                st.markdown(f"**Authors:** {paper['authors']}")
                st.markdown(f"**Published:** {paper['published']}")

                # Journal information (for PubMed articles)
                if paper.get('source') == 'PubMed' and paper.get('journal'):
                    journal_info = paper['journal']
                    if paper.get('volume') and paper.get('issue'):
                        journal_info += f", Vol. {paper['volume']}, Issue {paper['issue']}"
                    elif paper.get('volume'):
                        journal_info += f", Vol. {paper['volume']}"

                    # Check if it's a target journal
                    if is_high_impact_journal(paper['journal']):
                        st.markdown(f"**Journal:** {journal_info} ⭐")
                        st.markdown(
                            '<div style="color: #FFD700; font-weight: bold; font-size: 0.9em;">🌟 Relevant Journal</div>',
                            unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Journal:** {journal_info}")

                # Abstract (truncated)
                abstract = paper['abstract']
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
                st.markdown(f"**Abstract:** {abstract}")

                # Matched keywords
                if paper['matched_keywords']:
                    keywords_str = ", ".join(
                        [f"**{kw}**" for kw in paper['matched_keywords']])
                    st.markdown(f"**Matched Keywords:** {keywords_str}")

                # URL for debugging (can be removed later)
                if url:
                    st.caption(f"🔗 Link: {url}")

            with col2:
                # Source badge
                source = paper.get('source', 'arXiv')
                source_color = {
                    'arXiv': '#B31B1B',
                    'BioRxiv': '#00A86B',
                    'MedRxiv': '#0066CC',
                    'PubMed': '#FF6B35'
                }.get(source, '#666666')

                st.markdown(
                    f"<div style='text-align: center; margin-bottom: 10px;'>"
                    f"<span style='background-color: {source_color}; color: white; padding: 4px 8px; "
                    f"border-radius: 15px; font-size: 12px; font-weight: bold;'>{source}</span></div>",
                    unsafe_allow_html=True)

                # Relevance score
                score = paper['relevance_score']
                color = "green" if score >= 3 else "orange" if score >= 2 else "red"
                score_display = f"{score:.1f}" if isinstance(
                    score, (int, float)) else str(score)
                st.markdown(
                    f"<div style='text-align: center; padding: 10px; border: 2px solid {color}; border-radius: 10px;'>"
                    f"<h3 style='color: {color}; margin: 0;'>{score_display}</h3>"
                    f"<p style='margin: 0; font-size: 12px;'>Relevance Score</p></div>",
                    unsafe_allow_html=True)

            st.divider()

        # Close the special styling div for high-impact papers
        if is_high_impact:
            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
