"""Paper filtering and search functionality."""


import pandas as pd


class PaperFilter:
    """Handles filtering and searching of papers."""

    @staticmethod
    def apply_search_filter(
        papers_df: pd.DataFrame,
        search_query: str
    ) -> pd.DataFrame:
        """
        Apply text search filter to papers.
        
        Args:
            papers_df: DataFrame of papers
            search_query: Search query string
        
        Returns:
            Filtered DataFrame
        """
        if not search_query:
            return papers_df

        # Search in title, abstract, and authors
        mask = (
            papers_df["title"].str.contains(search_query, case=False, na=False) |
            papers_df["abstract"].str.contains(search_query, case=False, na=False) |
            papers_df["authors"].str.contains(search_query, case=False, na=False)
        )

        return papers_df[mask]

    @staticmethod
    def apply_journal_filter(
        papers_df: pd.DataFrame,
        high_impact_only: bool
    ) -> pd.DataFrame:
        """
        Filter papers by journal impact.
        
        Args:
            papers_df: DataFrame of papers
            high_impact_only: Whether to show only high-impact journal papers
        
        Returns:
            Filtered DataFrame
        """
        if not high_impact_only:
            return papers_df

        from utils.journal_utils import is_high_impact_journal

        # Filter for high-impact journals
        mask = papers_df.apply(
            lambda row: (
                row.get("source") == "PubMed" and
                row.get("journal") and
                is_high_impact_journal(row["journal"]) and
                len(row.get("matched_keywords", [])) >= 2
            ),
            axis=1
        )

        return papers_df[mask]

    @staticmethod
    def apply_keyword_filter(
        papers_df: pd.DataFrame,
        min_keyword_matches: int = 2
    ) -> pd.DataFrame:
        """
        Filter papers by minimum keyword matches.
        
        Args:
            papers_df: DataFrame of papers
            min_keyword_matches: Minimum number of keyword matches required
        
        Returns:
            Filtered DataFrame
        """
        mask = papers_df.apply(
            lambda row: len(row.get("matched_keywords", [])) >= min_keyword_matches,
            axis=1
        )

        return papers_df[mask]

    @staticmethod
    def get_filter_stats(
        original_df: pd.DataFrame,
        filtered_df: pd.DataFrame
    ) -> dict:
        """
        Get statistics about filtering results.
        
        Args:
            original_df: Original DataFrame before filtering
            filtered_df: DataFrame after filtering
        
        Returns:
            Dictionary with filter statistics
        """
        return {
            "original_count": len(original_df),
            "filtered_count": len(filtered_df),
            "excluded_count": len(original_df) - len(filtered_df),
            "exclusion_percentage": (
                (len(original_df) - len(filtered_df)) / len(original_df) * 100
                if len(original_df) > 0 else 0
            )
        }
