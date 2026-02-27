"""
Settings management service for the Manuscript Alert System.
Handles loading, saving, and updating settings that persist across app runs.
"""

import os
import re
from datetime import datetime
from typing import Any

from backend.src.utils.logger import Logger


# Initialize logger
logger = Logger(__name__)

class SettingsService:
    """Manages application settings with persistence to source files"""

    def __init__(self):
        self.settings_file = "backend/config/settings.py"
        self.backup_dir = "backend/config/backups"
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def load_settings(self) -> dict[str, Any]:
        """Load current settings from the settings.py file"""
        logger.info(">>> SettingsService.load_settings() called")
        try:
            # Import the settings module
            import importlib.util

            logger.debug(f"Loading settings from: {self.settings_file}")
            spec = importlib.util.spec_from_file_location("settings", self.settings_file)
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
                "must_have_keywords": getattr(settings_module, "MUST_HAVE_KEYWORDS", []),
            }

            logger.info(f"Settings loaded successfully: {len(settings_dict['keywords'])} keywords")
            logger.info("<<< SettingsService.load_settings() returning")
            return settings_dict
        except Exception as e:
            logger.error(f"Error loading settings: {e}", exc_info=True)
            logger.error(f"Error loading settings: {e}")
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
                }
            },
            "target_journals": {
                "exact_matches": ["jama", "nature", "science", "radiology", "ajnr", "the lancet"],
                "family_matches": ["jama ", "nature ", "science ", "npj ", "the lancet"],
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
                "abdominal", "pediatric", "cardiovascular and interventional",
                "interventional", "emergency", "skeletal", "clinical", "academic",
                "investigative", "case reports", "oral surgery", "korean journal of",
                "the neuroradiology", "japanese journal of", "brain research",
                "brain and behavior", "brain imaging and behavior", "brain stimulation",
                "brain connectivity", "brain and cognition", "brain, behavior, and immunity",
                "metabolic brain disease", "neuroscience letters", "neuroscience bulletin",
                "neuroscience methods", "neuroscience research", "neuroscience and biobehavioral",
                "clinical neuroscience", "neuropsychiatry", "ibro neuroscience",
                "acs chemical neuroscience", "proceedings of the national academy",
                "life science alliance", "life sciences", "animal science",
                "biomaterials science", "veterinary medical science",
                "philosophical transactions", "annals of the new york academy",
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

    def save_settings(self, settings: dict[str, Any]) -> bool:
        """Save settings to the settings.py file by completely rewriting it"""
        logger.warning(">>> SettingsService.save_settings() called")
        logger.info(f"Saving settings: {len(settings.get('keywords', []))} keywords")

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
            logger.error(f"Error saving settings: {e}")
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
            logger.warning(f"Could not create backup: {e}")

    def _update_keywords(self, content: str, keywords: list[str]) -> str:
        """Update the DEFAULT_KEYWORDS section"""
        keywords_str = "[\n" + "\n".join([f'    "{kw}",' for kw in keywords]) + "\n]"
        pattern = r"DEFAULT_KEYWORDS = \[.*?\]"
        replacement = f"DEFAULT_KEYWORDS = {keywords_str}"
        return re.sub(pattern, replacement, content, flags=re.DOTALL)

    def _update_journal_scoring(self, content: str, journal_scoring: dict[str, Any]) -> str:
        """Update the JOURNAL_SCORING section"""
        scoring_str = self._dict_to_python_string(journal_scoring, "JOURNAL_SCORING")
        pattern = r"JOURNAL_SCORING = \{.*?\}"
        return re.sub(pattern, scoring_str, content, flags=re.DOTALL)

    def _update_target_journals(self, content: str, target_journals: dict[str, list[str]]) -> str:
        """Update the TARGET_JOURNALS section"""
        journals_str = self._dict_to_python_string(target_journals, "TARGET_JOURNALS")
        pattern = r"TARGET_JOURNALS = \{.*?\}"
        return re.sub(pattern, journals_str, content, flags=re.DOTALL)

    def _update_journal_exclusions(self, content: str, exclusions: list[str]) -> str:
        """Update the JOURNAL_EXCLUSIONS section"""
        # Create a simple list format
        exclusions_str = "[\n" + "\n".join([f'    "{ex}",' for ex in exclusions]) + "\n]"

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
                content = content[:start_pos] + f"JOURNAL_EXCLUSIONS = {exclusions_str}" + content[end_pos:]
        else:
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        return content

    def _update_keyword_scoring(self, content: str, keyword_scoring: dict[str, Any]) -> str:
        """Update the KEYWORD_SCORING section"""
        scoring_str = self._dict_to_python_string(keyword_scoring, "KEYWORD_SCORING")
        pattern = r"KEYWORD_SCORING = \{.*?\}"
        return re.sub(pattern, scoring_str, content, flags=re.DOTALL)

    def _update_search_settings(self, content: str, search_settings: dict[str, Any]) -> str:
        """Update the DEFAULT_SEARCH_SETTINGS section"""
        settings_str = self._dict_to_python_string(search_settings, "DEFAULT_SEARCH_SETTINGS")
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
                return "{\n" + indent_str + (",\n" + indent_str).join(items) + "\n" + " " * indent + "}"

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
                return "[\n" + indent_str + (",\n" + indent_str).join(items) + "\n" + " " * indent + "]"

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

# Must-have keywords (required filter - papers must match at least one)
MUST_HAVE_KEYWORDS = {must_have_keywords}

# Default search settings
DEFAULT_SEARCH_SETTINGS = {search_settings}

# UI settings
UI_SETTINGS = {ui_settings}
'''

        # Format each section
        keywords_str = self._format_list(settings.get("keywords", []))
        journal_scoring_str = self._format_dict(settings.get("journal_scoring", {}))
        target_journals_str = self._format_dict(settings.get("target_journals", {}))
        journal_exclusions_str = self._format_list(settings.get("journal_exclusions", []))
        keyword_scoring_str = self._format_dict(settings.get("keyword_scoring", {}))
        must_have_keywords_str = self._format_list(settings.get("must_have_keywords", []))
        search_settings_str = self._format_dict(settings.get("search_settings", {}))
        ui_settings_str = self._format_dict(settings.get("ui_settings", {}))

        return content.format(
            keywords=keywords_str,
            journal_scoring=journal_scoring_str,
            target_journals=target_journals_str,
            journal_exclusions=journal_exclusions_str,
            keyword_scoring=keyword_scoring_str,
            must_have_keywords=must_have_keywords_str,
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
                return "{\n" + indent_str + (",\n" + indent_str).join(items) + "\n" + " " * indent + "}"

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
            logger.error(f"Error restoring backup: {e}")
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
