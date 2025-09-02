"""Service for exporting papers to various formats."""

from datetime import datetime

import pandas as pd


class ExportService:
    """Handles paper export functionality."""

    @staticmethod
    def generate_filename(
        papers_df: pd.DataFrame,
        filtered_count: int | None = None
    ) -> str:
        """
        Generate dynamic filename based on sources and filters.
        
        Args:
            papers_df: DataFrame of papers to export
            filtered_count: Number of papers after filtering (if different from total)
        
        Returns:
            Generated filename
        """
        if papers_df.empty:
            return f"papers_{datetime.now().strftime('%Y%m%d')}.csv"

        # Get unique sources
        sources = []
        if "source" in papers_df.columns:
            actual_sources = papers_df["source"].unique()

            # Map to lowercase for filename
            source_mapping = {
                "PubMed": "pubmed",
                "arXiv": "arxiv",
                "bioRxiv": "biorxiv",
                "medRxiv": "medrxiv"
            }

            for source in actual_sources:
                mapped = source_mapping.get(source, source.lower())
                sources.append(mapped)

        # Sort for consistent ordering
        sources.sort()
        sources_str = "_".join(sources) if sources else "papers"

        # Add filtered indicator if applicable
        filtered_suffix = ""
        if filtered_count is not None and filtered_count < len(papers_df):
            filtered_suffix = f"_filtered{filtered_count}"

        # Generate filename with date
        return f"{sources_str}{filtered_suffix}_{datetime.now().strftime('%Y%m%d')}.csv"

    @staticmethod
    def export_to_csv(papers_df: pd.DataFrame) -> str:
        """
        Export papers to CSV format.
        
        Args:
            papers_df: DataFrame of papers
        
        Returns:
            CSV string
        """
        return papers_df.to_csv(index=False)

    @staticmethod
    def export_to_json(papers_df: pd.DataFrame) -> str:
        """
        Export papers to JSON format.
        
        Args:
            papers_df: DataFrame of papers
        
        Returns:
            JSON string
        """
        return papers_df.to_json(orient="records", indent=2)

    @staticmethod
    def export_to_bibtex(papers_df: pd.DataFrame) -> str:
        """
        Export papers to BibTeX format.
        
        Args:
            papers_df: DataFrame of papers
        
        Returns:
            BibTeX string
        """
        bibtex_entries = []

        for _, paper in papers_df.iterrows():
            # Generate citation key
            first_author = paper["authors"].split(",")[0].split()[-1] if paper["authors"] else "Unknown"
            year = paper["published"][:4] if paper["published"] else "YYYY"
            title_word = paper["title"].split()[0] if paper["title"] else "Paper"
            cite_key = f"{first_author}{year}{title_word}"

            # Build BibTeX entry
            entry_type = "@article" if paper.get("journal") else "@misc"

            entry = [f"{entry_type}{{{cite_key},"]
            entry.append(f'  title = "{{{paper["title"]}}}",')
            entry.append(f'  author = "{{{paper["authors"]}}}",')
            entry.append(f'  year = "{{{year}}}",')

            if paper.get("journal"):
                entry.append(f'  journal = "{{{paper["journal"]}}}",')
            if paper.get("volume"):
                entry.append(f'  volume = "{{{paper["volume"]}}}",')
            if paper.get("pages"):
                entry.append(f'  pages = "{{{paper["pages"]}}}",')
            if paper.get("doi"):
                entry.append(f'  doi = "{{{paper["doi"]}}}",')
            if paper.get("abstract"):
                # Truncate abstract for BibTeX
                abstract = paper["abstract"][:500] + "..." if len(paper["abstract"]) > 500 else paper["abstract"]
                entry.append(f'  abstract = "{{{abstract}}}",')

            entry[-1] = entry[-1].rstrip(",")  # Remove last comma
            entry.append("}")

            bibtex_entries.append("\n".join(entry))

        return "\n\n".join(bibtex_entries)

    @staticmethod
    def get_export_stats(papers_df: pd.DataFrame) -> dict:
        """
        Get statistics about the export.
        
        Args:
            papers_df: DataFrame of papers
        
        Returns:
            Dictionary with export statistics
        """
        stats = {
            "total_papers": len(papers_df),
            "sources": {},
            "date_range": None
        }

        if not papers_df.empty:
            # Count by source
            if "source" in papers_df.columns:
                source_counts = papers_df["source"].value_counts()
                stats["sources"] = source_counts.to_dict()

            # Get date range
            if "published" in papers_df.columns:
                dates = pd.to_datetime(papers_df["published"], errors="coerce")
                valid_dates = dates.dropna()
                if not valid_dates.empty:
                    stats["date_range"] = {
                        "earliest": valid_dates.min().strftime("%Y-%m-%d"),
                        "latest": valid_dates.max().strftime("%Y-%m-%d")
                    }

        return stats
