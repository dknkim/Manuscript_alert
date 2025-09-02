"""Progress indicator component for multi-source fetching."""


import streamlit as st


class ProgressIndicator:
    """Handles progress indication for paper fetching."""

    # Source icon mapping
    SOURCE_ICONS = {
        "pubmed": "🏥",
        "arxiv": "📚",
        "biorxiv": "🧬",
        "medrxiv": "⚕️"
    }

    # Source display name mapping
    SOURCE_DISPLAY_MAP = {
        "pubmed": "PubMed",
        "arxiv": "arXiv",
        "biorxiv": "bioRxiv",
        "medrxiv": "medRxiv"
    }

    def __init__(self, source_names: list[str]):
        """
        Initialize progress indicators.
        
        Args:
            source_names: List of active source names
        """
        self.source_names = source_names
        self.progress_containers = {}

        if source_names:
            self._create_progress_bars()

    def _create_progress_bars(self):
        """Create compact horizontal progress bars for each source."""
        # Create a single compact container
        with st.container(border=True):
            st.markdown("**🔄 Fetching Papers**")

            # Create columns for each active source
            progress_cols = st.columns(len(self.source_names))

            # Initialize progress bars for each source
            for idx, source in enumerate(self.source_names):
                with progress_cols[idx]:
                    icon = self.SOURCE_ICONS.get(source, "📄")
                    st.caption(f"{icon} {source.upper()}")

                    progress_bar = st.progress(0)
                    status_placeholder = st.empty()
                    status_placeholder.caption("🔍 Starting...")

                    self.progress_containers[source] = {
                        "bar": progress_bar,
                        "status": status_placeholder,
                        "column": progress_cols[idx]
                    }

    def update_progress(self, source: str, progress: int, status: str):
        """
        Update progress for a specific source.
        
        Args:
            source: Source name
            progress: Progress value (0-100)
            status: Status message
        """
        if source in self.progress_containers:
            self.progress_containers[source]["bar"].progress(progress)
            self.progress_containers[source]["status"].caption(status)

    def show_fetching(self):
        """Show fetching status for all sources."""
        for source in self.source_names:
            self.update_progress(source, 20, "📥 Fetching papers...")

    def show_completion(self, papers_df):
        """
        Show completion status with paper counts.
        
        Args:
            papers_df: DataFrame of fetched papers
        """
        for source in self.source_names:
            # Update progress bar to complete
            self.progress_containers[source]["bar"].progress(100)

            # Count papers from this source
            display_name = self.SOURCE_DISPLAY_MAP.get(source, source.capitalize())
            source_count = 0

            if not papers_df.empty and "source" in papers_df.columns:
                source_count = len(papers_df[papers_df["source"] == display_name])

            # Update status with final count
            self.progress_containers[source]["status"].caption(
                f"✅ {source_count} papers"
            )

        # Show compact total summary
        if self.source_names:
            total_papers = len(papers_df) if not papers_df.empty else 0
            st.info(
                f"📋 Total: {total_papers} papers from {len(self.source_names)} sources"
            )
