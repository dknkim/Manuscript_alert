"""Paper filtering and search functionality."""

from __future__ import annotations

import pandas as pd


class PaperFilter:
    """Handles filtering and searching of papers."""

    @staticmethod
    def apply_search_filter(
        papers_df: pd.DataFrame,
        search_query: str,
    ) -> pd.DataFrame:
        """
        Apply text search filter to papers.

        Args:
            papers_df: DataFrame of papers.
            search_query: Search query string.

        Returns:
            Filtered DataFrame.
        """
        if not search_query:
            return papers_df

        mask: pd.Series = (  # type: ignore[type-arg]
            papers_df["title"].str.contains(search_query, case=False, na=False)
            | papers_df["abstract"].str.contains(search_query, case=False, na=False)
            | papers_df["authors"].str.contains(search_query, case=False, na=False)
        )
        return papers_df[mask]

    @staticmethod
    def apply_journal_filter(
        papers_df: pd.DataFrame,
        high_impact_only: bool,
    ) -> pd.DataFrame:
        """
        Filter papers by journal impact.

        Args:
            papers_df: DataFrame of papers.
            high_impact_only: Whether to show only high-impact journal papers.

        Returns:
            Filtered DataFrame.
        """
        if not high_impact_only:
            return papers_df

        from utils.journal_utils import is_high_impact_journal

        mask: pd.Series = papers_df.apply(  # type: ignore[type-arg]
            lambda row: (
                row.get("source") == "PubMed"
                and row.get("journal")
                and is_high_impact_journal(row["journal"])
                and len(row.get("matched_keywords", [])) >= 2
            ),
            axis=1,
        )
        return papers_df[mask]

    @staticmethod
    def apply_keyword_filter(
        papers_df: pd.DataFrame,
        min_keyword_matches: int = 2,
    ) -> pd.DataFrame:
        """
        Filter papers by minimum keyword matches.

        Args:
            papers_df: DataFrame of papers.
            min_keyword_matches: Minimum number of keyword matches required.

        Returns:
            Filtered DataFrame.
        """
        mask: pd.Series = papers_df.apply(  # type: ignore[type-arg]
            lambda row: len(row.get("matched_keywords", [])) >= min_keyword_matches,
            axis=1,
        )
        return papers_df[mask]

    @staticmethod
    def get_filter_stats(
        original_df: pd.DataFrame,
        filtered_df: pd.DataFrame,
    ) -> dict[str, int | float]:
        """
        Get statistics about filtering results.

        Args:
            original_df: Original DataFrame before filtering.
            filtered_df: DataFrame after filtering.

        Returns:
            Dictionary with filter statistics.
        """
        orig_len: int = len(original_df)
        filt_len: int = len(filtered_df)
        return {
            "original_count": orig_len,
            "filtered_count": filt_len,
            "excluded_count": orig_len - filt_len,
            "exclusion_percentage": (
                (orig_len - filt_len) / orig_len * 100 if orig_len > 0 else 0.0
            ),
        }
