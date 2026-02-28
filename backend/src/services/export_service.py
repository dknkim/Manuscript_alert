"""Service for exporting papers to various formats."""

from __future__ import annotations

from datetime import datetime

import pandas as pd


class ExportService:
    """Handles paper export functionality."""

    @staticmethod
    def generate_filename(
        papers_df: pd.DataFrame,
        filtered_count: int | None = None,
    ) -> str:
        """
        Generate a dynamic filename based on sources and filters.

        Args:
            papers_df: DataFrame of papers to export.
            filtered_count: Number of papers after filtering (if different from total).

        Returns:
            Generated filename string.
        """
        if papers_df.empty:
            return f"papers_{datetime.now().strftime('%Y%m%d')}.csv"

        sources: list[str] = []
        if "source" in papers_df.columns:
            actual_sources: pd.Index = papers_df["source"].unique()
            source_mapping: dict[str, str] = {
                "PubMed": "pubmed",
                "arXiv": "arxiv",
                "bioRxiv": "biorxiv",
                "medRxiv": "medrxiv",
            }
            for source in actual_sources:
                mapped: str = source_mapping.get(source, source.lower())
                sources.append(mapped)

        sources.sort()
        sources_str: str = "_".join(sources) if sources else "papers"

        filtered_suffix: str = ""
        if filtered_count is not None and filtered_count < len(papers_df):
            filtered_suffix = f"_filtered{filtered_count}"

        return f"{sources_str}{filtered_suffix}_{datetime.now().strftime('%Y%m%d')}.csv"

    @staticmethod
    def export_to_csv(papers_df: pd.DataFrame) -> str:
        """Export papers to CSV format."""
        return papers_df.to_csv(index=False)

    @staticmethod
    def export_to_json(papers_df: pd.DataFrame) -> str:
        """Export papers to JSON format."""
        return papers_df.to_json(orient="records", indent=2)

    @staticmethod
    def export_to_bibtex(papers_df: pd.DataFrame) -> str:
        """Export papers to BibTeX format."""
        bibtex_entries: list[str] = []

        for _, paper in papers_df.iterrows():
            first_author: str = (
                paper["authors"].split(",")[0].split()[-1]
                if paper["authors"]
                else "Unknown"
            )
            year: str = paper["published"][:4] if paper["published"] else "YYYY"
            title_word: str = paper["title"].split()[0] if paper["title"] else "Paper"
            cite_key: str = f"{first_author}{year}{title_word}"

            entry_type: str = "@article" if paper.get("journal") else "@misc"

            entry: list[str] = [f"{entry_type}{{{cite_key},"]
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
                abstract: str = (
                    paper["abstract"][:500] + "..."
                    if len(paper["abstract"]) > 500
                    else paper["abstract"]
                )
                entry.append(f'  abstract = "{{{abstract}}}",')

            entry[-1] = entry[-1].rstrip(",")
            entry.append("}")
            bibtex_entries.append("\n".join(entry))

        return "\n\n".join(bibtex_entries)

    @staticmethod
    def get_export_stats(papers_df: pd.DataFrame) -> dict[str, object]:
        """
        Get statistics about the export.

        Args:
            papers_df: DataFrame of papers.

        Returns:
            Dictionary with export statistics.
        """
        stats: dict[str, object] = {
            "total_papers": len(papers_df),
            "sources": {},
            "date_range": None,
        }

        if not papers_df.empty:
            if "source" in papers_df.columns:
                source_counts: pd.Series = papers_df["source"].value_counts()  # type: ignore[type-arg]
                stats["sources"] = source_counts.to_dict()

            if "published" in papers_df.columns:
                dates: pd.Series = pd.to_datetime(  # type: ignore[type-arg]
                    papers_df["published"], errors="coerce"
                )
                valid_dates: pd.Series = dates.dropna()  # type: ignore[type-arg]
                if not valid_dates.empty:
                    stats["date_range"] = {
                        "earliest": valid_dates.min().strftime("%Y-%m-%d"),
                        "latest": valid_dates.max().strftime("%Y-%m-%d"),
                    }

        return stats
