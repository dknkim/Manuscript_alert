"""
Settings management service for the Manuscript Alert System.
Handles loading, saving, and updating settings that persist across app runs.

After Phase 2.1 refactor: Settings are stored in separate user_preferences table
with structured columns for better querying, indexing, and type safety.
"""

import os
import re
from datetime import datetime
from typing import Any

import streamlit as st

from utils.logger import Logger


# Initialize logger
logger = Logger(__name__)


class SettingsService:
    """Manages application settings with persistence to Supabase user profiles"""

    def __init__(self, use_supabase=True):
        """
        Initialize SettingsService.

        Args:
            use_supabase: If True, use Supabase for storage. If False, use legacy settings.py file.
        """
        self.use_supabase = use_supabase
        self.settings_file = "config/settings.py"
        self.backup_dir = "config/backups"
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def load_settings(self, user_id: str = None) -> dict[str, Any]:
        """
        Load settings - from Supabase user profile or legacy settings.py file.

        Args:
            user_id: User ID to load settings for (required if use_supabase=True)

        Returns:
            Dict containing all user settings
        """
        logger.info(">>> SettingsService.load_settings() called")

        if self.use_supabase:
            return self._load_settings_from_supabase(user_id)
        else:
            return self._load_settings_from_file()

    def _load_settings_from_supabase(self, user_id: str) -> dict[str, Any]:
        """Load settings from Supabase user_preferences table"""
        if not user_id:
            logger.error("user_id required for Supabase settings")
            return self._get_default_settings()

        try:
            from services.supabase_client import get_supabase_admin_client

            logger.debug(
                f"Loading settings from Supabase user_preferences table for user: {user_id}"
            )
            admin_client = get_supabase_admin_client()

            # Load from structured user_preferences table
            result = (
                admin_client.table("user_preferences")
                .select("*")
                .eq("user_id", user_id)
                .single()
                .execute()
            )

            if result.data:
                # Transform table columns to dict format expected by app
                preferences = self._table_to_dict(result.data)
                logger.info(
                    f"Settings loaded from user_preferences table: {len(preferences.get('keywords', []))} keywords"
                )
                return preferences
            else:
                logger.warning(
                    f"No preferences found in table for user {user_id}, using defaults"
                )
                return self._get_default_settings()

        except Exception as e:
            logger.error(
                f"Error loading settings from user_preferences table: {e}",
                exc_info=True,
            )
            return self._get_default_settings()

    def _load_settings_from_file(self) -> dict[str, Any]:
        """Load settings from legacy settings.py file"""
        logger.info("Loading settings from legacy settings.py file")
        try:
            # Import the settings module
            import importlib.util

            logger.debug(f"Loading settings from: {self.settings_file}")
            spec = importlib.util.spec_from_file_location(
                "settings", self.settings_file
            )
            settings_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings_module)

            settings_dict = {
                "keywords": settings_module.DEFAULT_KEYWORDS,
                "journal_scoring": settings_module.JOURNAL_SCORING,
                "target_journals": settings_module.TARGET_JOURNALS,
                "journal_exclusions": settings_module.JOURNAL_EXCLUSIONS,
                "keyword_scoring": settings_module.KEYWORD_SCORING,
                "search_settings": settings_module.DEFAULT_SEARCH_SETTINGS,
                "ui_settings": settings_module.UI_SETTINGS,
            }

            logger.info(
                f"Settings loaded successfully: {len(settings_dict['keywords'])} keywords"
            )
            logger.info("<<< SettingsService.load_settings() returning")
            return settings_dict
        except Exception as e:
            logger.error(f"Error loading settings: {e}", exc_info=True)
            st.error(f"Error loading settings: {e}")
            return self._get_default_settings()

    def _get_default_settings(self) -> dict[str, Any]:
        """Get default settings if loading fails"""
        return {
            "keywords": [
                "Alzheimer's disease",
                "PET",
                "MRI",
                "dementia",
                "amyloid",
                "tau",
                "plasma",
                "brain",
            ],
            "journal_scoring": {
                "enabled": True,
                "high_impact_journal_boost": {
                    "5_or_more_keywords": 5.1,
                    "4_keywords": 3.7,
                    "3_keywords": 2.8,
                    "2_keywords": 1.3,
                    "1_keyword": 0.5,
                },
            },
            "target_journals": {
                "exact_matches": [
                    "jama",
                    "nature",
                    "science",
                    "radiology",
                    "ajnr",
                    "the lancet",
                ],
                "family_matches": [
                    "jama ",
                    "nature ",
                    "science ",
                    "npj ",
                    "the lancet",
                ],
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
                    "brain : a journal of neurology",
                ],
            },
            "journal_exclusions": [
                "abdominal",
                "pediatric",
                "cardiovascular and interventional",
                "interventional",
                "emergency",
                "skeletal",
                "clinical",
                "academic",
                "investigative",
                "case reports",
                "oral surgery",
                "korean journal of",
                "the neuroradiology",
                "japanese journal of",
                "brain research",
                "brain and behavior",
                "brain imaging and behavior",
                "brain stimulation",
                "brain connectivity",
                "brain and cognition",
                "brain, behavior, and immunity",
                "metabolic brain disease",
                "neuroscience letters",
                "neuroscience bulletin",
                "neuroscience methods",
                "neuroscience research",
                "neuroscience and biobehavioral",
                "clinical neuroscience",
                "neuropsychiatry",
                "ibro neuroscience",
                "acs chemical neuroscience",
                "proceedings of the national academy",
                "life science alliance",
                "life sciences",
                "animal science",
                "biomaterials science",
                "veterinary medical science",
                "philosophical transactions",
                "annals of the new york academy",
            ],
            "keyword_scoring": {
                "high_priority": {
                    "keywords": ["Alzheimer's disease", "dementia", "amyloid", "tau"],
                    "boost": 1.5,
                },
                "medium_priority": {
                    "keywords": ["PET", "MRI", "brain", "plasma"],
                    "boost": 1.2,
                },
                "low_priority": {
                    "keywords": ["neuroimaging", "cognition", "memory"],
                    "boost": 1.0,
                },
            },
            "search_settings": {
                "days_back": 7,
                "search_mode": "Brief",
                "min_keyword_matches": 2,
                "max_results_display": 50,
                "default_sources": {
                    "pubmed": True,
                    "arxiv": False,
                    "biorxiv": False,
                    "medrxiv": False,
                },
                "journal_quality_filter": False,
            },
            "ui_settings": {
                "theme": "light",
                "show_abstracts": True,
                "show_keywords": True,
                "show_relevance_scores": True,
                "papers_per_page": 50,
            },
        }

    def _table_to_dict(self, table_row: dict[str, Any]) -> dict[str, Any]:
        """
        Transform user_preferences table row to settings dict format.

        Args:
            table_row: Row from user_preferences table

        Returns:
            Settings dict in app format
        """
        return {
            "keywords": table_row.get("keywords", []),
            "target_journals": table_row.get("target_journals", {}),
            "journal_exclusions": table_row.get("journal_exclusions", []),
            "journal_scoring": table_row.get("journal_scoring", {}),
            "keyword_scoring": table_row.get("keyword_scoring", {}),
            "search_settings": {
                "search_days_back": table_row.get("search_days_back", 8),
                "search_mode": table_row.get("search_mode", "Brief"),
                "min_keyword_matches": table_row.get("min_keyword_matches", 2),
                "max_results_display": table_row.get("max_results_display", 50),
                "default_sources": {
                    "pubmed": table_row.get("default_source_pubmed", True),
                    "arxiv": table_row.get("default_source_arxiv", False),
                    "biorxiv": table_row.get("default_source_biorxiv", True),
                    "medrxiv": table_row.get("default_source_medrxiv", True),
                },
                "journal_quality_filter": table_row.get(
                    "journal_quality_filter", False
                ),
            },
            "ui_preferences": {
                "theme": table_row.get("theme", "light"),
                "notifications_enabled": table_row.get("notifications_enabled", True),
                "email_alerts": table_row.get("email_alerts", False),
            },
            "display_settings": {
                "show_abstracts": table_row.get("show_abstracts", True),
                "show_keywords": table_row.get("show_keywords", True),
                "show_relevance_scores": table_row.get("show_relevance_scores", True),
                "papers_per_page": table_row.get("papers_per_page", 50),
            },
        }

    def _dict_to_table(self, settings: dict[str, Any]) -> dict[str, Any]:
        """
        Transform settings dict to user_preferences table columns.

        Args:
            settings: Settings dict in app format

        Returns:
            Dict matching user_preferences table schema
        """
        ui_prefs = settings.get("ui_preferences", {})
        search = settings.get("search_settings", {})
        sources = search.get("default_sources", {})
        display = settings.get("display_settings", {})

        return {
            # UI Preferences
            "theme": ui_prefs.get("theme", "light"),
            "notifications_enabled": ui_prefs.get("notifications_enabled", True),
            "email_alerts": ui_prefs.get("email_alerts", False),
            # Research Keywords
            "keywords": settings.get("keywords", []),
            # Journal Settings (JSONB)
            "target_journals": settings.get("target_journals", {}),
            "journal_exclusions": settings.get("journal_exclusions", []),
            "journal_scoring": settings.get("journal_scoring", {}),
            "keyword_scoring": settings.get("keyword_scoring", {}),
            # Search Settings
            "search_days_back": search.get("search_days_back", 8),
            "search_mode": search.get("search_mode", "Brief"),
            "min_keyword_matches": search.get("min_keyword_matches", 2),
            "max_results_display": search.get("max_results_display", 50),
            # Default Sources
            "default_source_pubmed": sources.get("pubmed", True),
            "default_source_arxiv": sources.get("arxiv", False),
            "default_source_biorxiv": sources.get("biorxiv", True),
            "default_source_medrxiv": sources.get("medrxiv", True),
            "journal_quality_filter": search.get("journal_quality_filter", False),
            # Display Settings
            "show_abstracts": display.get("show_abstracts", True),
            "show_keywords": display.get("show_keywords", True),
            "show_relevance_scores": display.get("show_relevance_scores", True),
            "papers_per_page": display.get("papers_per_page", 50),
            # Update timestamp
            "updated_at": "now()",
        }

    def save_settings(self, settings: dict[str, Any], user_id: str = None) -> bool:
        """
        Save settings - to Supabase user profile or legacy settings.py file.

        Args:
            settings: Dict containing all settings to save
            user_id: User ID to save settings for (required if use_supabase=True)

        Returns:
            True if successful, False otherwise
        """
        logger.warning(">>> SettingsService.save_settings() called")
        logger.info(f"Saving settings: {len(settings.get('keywords', []))} keywords")

        if self.use_supabase:
            return self._save_settings_to_supabase(settings, user_id)
        else:
            return self._save_settings_to_file(settings)

    def _save_settings_to_supabase(
        self, settings: dict[str, Any], user_id: str
    ) -> bool:
        """Save settings to Supabase user_preferences table"""
        if not user_id:
            logger.error("user_id required for Supabase settings")
            st.error("Cannot save settings: user not identified")
            return False

        try:
            from services.supabase_client import get_supabase_admin_client

            logger.debug(
                f"Saving settings to user_preferences table for user: {user_id}"
            )
            admin_client = get_supabase_admin_client()

            # Transform dict format to table columns
            table_data = self._dict_to_table(settings)

            # Update user_preferences table
            result = (
                admin_client.table("user_preferences")
                .update(table_data)
                .eq("user_id", user_id)
                .execute()
            )

            if result.data:
                logger.warning(
                    "✅ Settings saved to user_preferences table successfully!"
                )
                return True
            else:
                logger.error("Failed to save settings to user_preferences table")
                st.error("Failed to save settings")
                return False

        except Exception as e:
            logger.error(
                f"❌ Error saving settings to user_preferences table: {e}",
                exc_info=True,
            )
            st.error(f"Error saving settings: {e}")
            return False

    def _save_settings_to_file(self, settings: dict[str, Any]) -> bool:
        """Save settings to legacy settings.py file"""
        logger.info("Saving settings to legacy settings.py file")
        try:
            # Create backup first
            logger.debug("Creating backup before save...")
            self._create_backup()

            # Generate the complete settings file content
            logger.debug("Generating settings file content...")
            content = self._generate_settings_file(settings)
            logger.debug(f"Generated content length: {len(content)} chars")

            # Write the complete file
            logger.info(f"Writing settings to: {self.settings_file}")
            with open(self.settings_file, "w", encoding="utf-8") as f:
                f.write(content)

            logger.warning("✅ Settings saved successfully!")
            logger.warning("<<< SettingsService.save_settings() returning True")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving settings: {e}", exc_info=True)
            st.error(f"Error saving settings: {e}")
            return False

    def _create_backup(self):
        """Create a backup of the current settings file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"settings_backup_{timestamp}.py")

        try:
            with open(self.settings_file, encoding="utf-8") as src:
                with open(backup_file, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
        except Exception as e:
            st.warning(f"Could not create backup: {e}")

    def _update_keywords(self, content: str, keywords: list[str]) -> str:
        """Update the DEFAULT_KEYWORDS section"""
        keywords_str = "[\n" + "\n".join([f'    "{kw}",' for kw in keywords]) + "\n]"
        pattern = r"DEFAULT_KEYWORDS = \[.*?\]"
        replacement = f"DEFAULT_KEYWORDS = {keywords_str}"
        return re.sub(pattern, replacement, content, flags=re.DOTALL)

    def _update_journal_scoring(
        self, content: str, journal_scoring: dict[str, Any]
    ) -> str:
        """Update the JOURNAL_SCORING section"""
        scoring_str = self._dict_to_python_string(journal_scoring, "JOURNAL_SCORING")
        pattern = r"JOURNAL_SCORING = \{.*?\}"
        return re.sub(pattern, scoring_str, content, flags=re.DOTALL)

    def _update_target_journals(
        self, content: str, target_journals: dict[str, list[str]]
    ) -> str:
        """Update the TARGET_JOURNALS section"""
        journals_str = self._dict_to_python_string(target_journals, "TARGET_JOURNALS")
        pattern = r"TARGET_JOURNALS = \{.*?\}"
        return re.sub(pattern, journals_str, content, flags=re.DOTALL)

    def _update_journal_exclusions(self, content: str, exclusions: list[str]) -> str:
        """Update the JOURNAL_EXCLUSIONS section"""
        # Create a simple list format
        exclusions_str = (
            "[\n" + "\n".join([f'    "{ex}",' for ex in exclusions]) + "\n]"
        )

        # Use a more specific pattern that matches the entire JOURNAL_EXCLUSIONS assignment
        pattern = r"JOURNAL_EXCLUSIONS = \[.*?\]"
        replacement = f"JOURNAL_EXCLUSIONS = {exclusions_str}"

        # If the pattern doesn't match, try to find and replace the whole section
        if not re.search(pattern, content, flags=re.DOTALL):
            # Find the start and end of the JOURNAL_EXCLUSIONS section
            start_pattern = r"JOURNAL_EXCLUSIONS = \["
            end_pattern = r"\]"

            start_match = re.search(start_pattern, content)
            if start_match:
                start_pos = start_match.start()
                # Find the matching closing bracket
                bracket_count = 0
                end_pos = start_pos
                for i, char in enumerate(content[start_pos:], start_pos):
                    if char == "[":
                        bracket_count += 1
                    elif char == "]":
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i + 1
                            break

                # Replace the entire section
                content = (
                    content[:start_pos]
                    + f"JOURNAL_EXCLUSIONS = {exclusions_str}"
                    + content[end_pos:]
                )
        else:
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        return content

    def _update_keyword_scoring(
        self, content: str, keyword_scoring: dict[str, Any]
    ) -> str:
        """Update the KEYWORD_SCORING section"""
        scoring_str = self._dict_to_python_string(keyword_scoring, "KEYWORD_SCORING")
        pattern = r"KEYWORD_SCORING = \{.*?\}"
        return re.sub(pattern, scoring_str, content, flags=re.DOTALL)

    def _update_search_settings(
        self, content: str, search_settings: dict[str, Any]
    ) -> str:
        """Update the DEFAULT_SEARCH_SETTINGS section"""
        settings_str = self._dict_to_python_string(
            search_settings, "DEFAULT_SEARCH_SETTINGS"
        )
        pattern = r"DEFAULT_SEARCH_SETTINGS = \{.*?\}"
        return re.sub(pattern, settings_str, content, flags=re.DOTALL)

    def _update_ui_settings(self, content: str, ui_settings: dict[str, Any]) -> str:
        """Update the UI_SETTINGS section"""
        settings_str = self._dict_to_python_string(ui_settings, "UI_SETTINGS")
        pattern = r"UI_SETTINGS = \{.*?\}"
        return re.sub(pattern, settings_str, content, flags=re.DOTALL)

    def _dict_to_python_string(self, data: dict[str, Any], var_name: str) -> str:
        """Convert a dictionary to a properly formatted Python string"""

        def format_value(value, indent=0):
            if isinstance(value, dict):
                if not value:
                    return "{}"
                items = []
                for k, v in value.items():
                    key_str = f'"{k}"'
                    if isinstance(v, dict):
                        val_str = format_value(v, indent + 4)
                    elif isinstance(v, list):
                        val_str = format_value(v, indent + 4)
                    elif isinstance(v, str):
                        val_str = f'"{v}"'
                    elif isinstance(v, bool):
                        val_str = "True" if v else "False"
                    else:
                        val_str = str(v)
                    items.append(f"{key_str}: {val_str}")

                indent_str = " " * (indent + 4)
                return (
                    "{\n"
                    + indent_str
                    + (",\n" + indent_str).join(items)
                    + "\n"
                    + " " * indent
                    + "}"
                )

            elif isinstance(value, list):
                if not value:
                    return "[]"
                items = []
                for item in value:
                    if isinstance(item, str):
                        items.append(f'"{item}"')
                    elif isinstance(item, dict):
                        items.append(format_value(item, indent + 4))
                    elif isinstance(item, list):
                        items.append(format_value(item, indent + 4))
                    else:
                        items.append(str(item))

                indent_str = " " * (indent + 4)
                return (
                    "[\n"
                    + indent_str
                    + (",\n" + indent_str).join(items)
                    + "\n"
                    + " " * indent
                    + "]"
                )

            elif isinstance(value, str):
                return f'"{value}"'
            elif isinstance(value, bool):
                return "True" if value else "False"
            else:
                return str(value)

        return f"{var_name} = {format_value(data)}"

    def _generate_settings_file(self, settings: dict[str, Any]) -> str:
        """Generate the complete settings file content"""
        content = '''"""
Settings configuration for the Manuscript Alert System.
This file contains all configurable settings that can be modified through the UI.
"""

# Default keywords for research alerts
DEFAULT_KEYWORDS = {keywords}

# Journal scoring configuration
JOURNAL_SCORING = {journal_scoring}

# Target journal patterns with priority levels
TARGET_JOURNALS = {target_journals}

# Simplified journal exclusions - all patterns apply to all journal types
JOURNAL_EXCLUSIONS = {journal_exclusions}

# Keyword-specific scoring (for future enhancement)
KEYWORD_SCORING = {keyword_scoring}

# Default search settings
DEFAULT_SEARCH_SETTINGS = {search_settings}

# UI settings
UI_SETTINGS = {ui_settings}
'''

        # Format each section
        keywords_str = self._format_list(settings.get("keywords", []))
        journal_scoring_str = self._format_dict(settings.get("journal_scoring", {}))
        target_journals_str = self._format_dict(settings.get("target_journals", {}))
        journal_exclusions_str = self._format_list(
            settings.get("journal_exclusions", [])
        )
        keyword_scoring_str = self._format_dict(settings.get("keyword_scoring", {}))
        search_settings_str = self._format_dict(settings.get("search_settings", {}))
        ui_settings_str = self._format_dict(settings.get("ui_settings", {}))

        return content.format(
            keywords=keywords_str,
            journal_scoring=journal_scoring_str,
            target_journals=target_journals_str,
            journal_exclusions=journal_exclusions_str,
            keyword_scoring=keyword_scoring_str,
            search_settings=search_settings_str,
            ui_settings=ui_settings_str,
        )

    def _format_list(self, items: list[str]) -> str:
        """Format a list of strings for Python code"""
        if not items:
            return "[]"
        return "[\n" + "\n".join([f'    "{item}",' for item in items]) + "\n]"

    def _format_dict(self, data: dict[str, Any]) -> str:
        """Format a dictionary for Python code"""
        if not data:
            return "{}"

        def format_value(value, indent=0):
            if isinstance(value, dict):
                if not value:
                    return "{}"
                items = []
                for k, v in value.items():
                    key_str = f'"{k}"'
                    if isinstance(v, dict):
                        val_str = format_value(v, indent + 4)
                    elif isinstance(v, list):
                        val_str = self._format_list(v)
                    elif isinstance(v, str):
                        val_str = f'"{v}"'
                    elif isinstance(v, bool):
                        val_str = "True" if v else "False"
                    else:
                        val_str = str(v)
                    items.append(f"{key_str}: {val_str}")

                indent_str = " " * (indent + 4)
                return (
                    "{\n"
                    + indent_str
                    + (",\n" + indent_str).join(items)
                    + "\n"
                    + " " * indent
                    + "}"
                )

            elif isinstance(value, list):
                return self._format_list(value)
            elif isinstance(value, str):
                return f'"{value}"'
            elif isinstance(value, bool):
                return "True" if value else "False"
            else:
                return str(value)

        return format_value(data)

    def restore_backup(self, backup_file: str) -> bool:
        """Restore settings from a backup file"""
        try:
            with open(backup_file, encoding="utf-8") as src:
                content = src.read()

            with open(self.settings_file, "w", encoding="utf-8") as dst:
                dst.write(content)

            return True
        except Exception as e:
            st.error(f"Error restoring backup: {e}")
            return False

    def list_backups(self) -> list[str]:
        """List available backup files"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith("settings_backup_") and file.endswith(".py"):
                    backup_files.append(os.path.join(self.backup_dir, file))
            return sorted(backup_files, reverse=True)  # Most recent first
        except Exception:
            return []
