"""Tests for journal utility functions."""

from __future__ import annotations

from backend.src.utils.journal_utils import (
    get_high_impact_journal_list,
    get_journal_category,
    is_high_impact_journal,
)


class TestIsHighImpactJournal:
    def test_nature(self) -> None:
        assert is_high_impact_journal("Nature Medicine") is True

    def test_jama(self) -> None:
        assert is_high_impact_journal("JAMA Neurology") is True

    def test_lancet(self) -> None:
        assert is_high_impact_journal("The Lancet") is True

    def test_nejm(self) -> None:
        assert is_high_impact_journal("New England Journal of Medicine") is True

    def test_alzheimers(self) -> None:
        assert is_high_impact_journal("Alzheimer's & Dementia") is True

    def test_radiology(self) -> None:
        assert is_high_impact_journal("Radiology") is True

    def test_low_impact(self) -> None:
        assert is_high_impact_journal("Journal of Obscure Studies") is False

    def test_empty_string(self) -> None:
        assert is_high_impact_journal("") is False

    def test_none_returns_false(self) -> None:
        assert is_high_impact_journal(None) is False  # type: ignore[arg-type]

    def test_case_insensitive(self) -> None:
        assert is_high_impact_journal("NATURE MEDICINE") is True
        assert is_high_impact_journal("nature medicine") is True


class TestGetJournalCategory:
    def test_nature_category(self) -> None:
        assert get_journal_category("Nature Neuroscience") == "nature"

    def test_jama_category(self) -> None:
        assert get_journal_category("JAMA") == "jama"

    def test_other_category(self) -> None:
        assert get_journal_category("Random Journal") == "other"

    def test_empty_string(self) -> None:
        assert get_journal_category("") == "other"

    def test_none_returns_other(self) -> None:
        assert get_journal_category(None) == "other"  # type: ignore[arg-type]


class TestGetHighImpactJournalList:
    def test_returns_sorted_list(self) -> None:
        patterns = get_high_impact_journal_list()
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        assert patterns == sorted(patterns)

    def test_contains_known_patterns(self) -> None:
        patterns = get_high_impact_journal_list()
        assert "nature" in patterns
        assert "lancet" in patterns
        assert "radiology" in patterns
