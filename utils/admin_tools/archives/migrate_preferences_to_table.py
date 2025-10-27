#!/usr/bin/env python3
"""
Migration script to move user preferences from JSONB blob to structured table.

This script:
1. Reads existing user_profiles.preferences JSONB data
2. Transforms it to match the new user_preferences table schema
3. Inserts data into user_preferences table
4. Verifies migration success
5. Provides detailed migration report

Usage:
    python utils/admin_tools/migrate_preferences_to_table.py
"""

import sys
from pathlib import Path


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.supabase_client import get_supabase_admin_client
from utils.logger import Logger


logger = Logger(__name__)


class PreferencesMigrator:
    """Migrates user preferences from JSONB blob to structured table."""

    def __init__(self):
        """Initialize migrator with Supabase admin client."""
        self.client = get_supabase_admin_client()
        self.migration_stats = {
            "total_users": 0,
            "migrated": 0,
            "skipped": 0,
            "errors": 0,
            "error_details": [],
        }

    def get_users_with_preferences(self):
        """Fetch all users with their current JSONB preferences."""
        try:
            response = (
                self.client.table("user_profiles")
                .select("id, preferences")
                .not_.is_("preferences", "null")
                .execute()
            )

            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch users: {e}")
            raise

    def transform_preferences(self, user_id: str, prefs_jsonb: dict) -> dict:
        """
        Transform JSONB preferences to structured table columns.

        Args:
            user_id: User's UUID
            prefs_jsonb: Current JSONB preferences object

        Returns:
            Dictionary matching user_preferences table schema
        """
        # Extract UI preferences
        ui_prefs = prefs_jsonb.get("ui_preferences", {})

        # Extract search settings
        search = prefs_jsonb.get("search_settings", {})

        # Extract default sources
        sources = search.get("default_sources", {})

        # Extract display settings
        display = prefs_jsonb.get("display_settings", {})

        # Build structured data matching table schema
        return {
            "user_id": user_id,
            # UI Preferences
            "theme": ui_prefs.get("theme", "light"),
            "notifications_enabled": ui_prefs.get("notifications_enabled", True),
            "email_alerts": ui_prefs.get("email_alerts", False),
            # Research Keywords (array)
            "keywords": prefs_jsonb.get(
                "keywords",
                ["Alzheimer's disease", "PET", "amyloid", "tau", "plasma", "brain"],
            ),
            # Journal Settings (keep as JSONB)
            "target_journals": prefs_jsonb.get(
                "target_journals",
                {
                    "exact_matches": [
                        "jama",
                        "nature",
                        "science",
                        "radiology",
                        "ajnr",
                        "the lancet",
                    ],
                    "family_matches": [
                        "jama",
                        "nature",
                        "science",
                        "npj",
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
            ),
            "journal_exclusions": prefs_jsonb.get(
                "journal_exclusions",
                [
                    "abdominal",
                    "pediatric",
                    "cardiovascular and interventional",
                    "interventional",
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
                    "veterinary medical science",
                    "philosophical transactions",
                    "annals of the new york academy",
                ],
            ),
            "journal_scoring": prefs_jsonb.get(
                "journal_scoring",
                {
                    "enabled": True,
                    "high_impact_journal_boost": {
                        "5_or_more_keywords": 4.9,
                        "4_keywords": 3.7,
                        "3_keywords": 2.8,
                        "2_keywords": 1.0,
                        "1_keyword": 0.1,
                    },
                },
            ),
            # Keyword Scoring (keep as JSONB)
            "keyword_scoring": prefs_jsonb.get(
                "keyword_scoring",
                {
                    "high_priority": {
                        "keywords": ["Alzheimer's disease", "amyloid"],
                        "boost": 1.5,
                    },
                    "medium_priority": {
                        "keywords": ["PET", "brain", "plasma"],
                        "boost": 1.2,
                    },
                },
            ),
            # Search Settings (individual columns)
            "search_days_back": search.get("search_days_back", 8),
            "search_mode": search.get("search_mode", "Brief"),
            "min_keyword_matches": search.get("min_keyword_matches", 2),
            "max_results_display": search.get("max_results_display", 50),
            # Default Sources (boolean columns)
            "default_source_pubmed": sources.get("pubmed", True),
            "default_source_arxiv": sources.get("arxiv", False),
            "default_source_biorxiv": sources.get("biorxiv", True),
            "default_source_medrxiv": sources.get("medrxiv", True),
            "journal_quality_filter": search.get("journal_quality_filter", False),
            # UI Display Settings
            "show_abstracts": display.get("show_abstracts", True),
            "show_keywords": display.get("show_keywords", True),
            "show_relevance_scores": display.get("show_relevance_scores", True),
            "papers_per_page": display.get("papers_per_page", 50),
        }

    def migrate_user(self, user_id: str, prefs_jsonb: dict) -> bool:
        """
        Migrate single user's preferences.

        Args:
            user_id: User's UUID
            prefs_jsonb: Current JSONB preferences

        Returns:
            True if migration successful, False otherwise
        """
        try:
            # Check if user already has preferences in new table
            existing = (
                self.client.table("user_preferences")
                .select("id")
                .eq("user_id", user_id)
                .execute()
            )

            if existing.data:
                logger.info(
                    f"User {user_id} already has preferences in table, skipping"
                )
                self.migration_stats["skipped"] += 1
                return True

            # Transform and insert
            structured_prefs = self.transform_preferences(user_id, prefs_jsonb)

            self.client.table("user_preferences").insert(structured_prefs).execute()

            logger.info(f"Successfully migrated preferences for user {user_id}")
            self.migration_stats["migrated"] += 1
            return True

        except Exception as e:
            logger.error(f"Failed to migrate user {user_id}: {e}")
            self.migration_stats["errors"] += 1
            self.migration_stats["error_details"].append(
                {"user_id": user_id, "error": str(e)}
            )
            return False

    def verify_migration(self) -> bool:
        """
        Verify migration completed successfully.

        Returns:
            True if verification passed
        """
        try:
            # Count user_profiles with preferences
            profiles_count = (
                self.client.table("user_profiles")
                .select("id", count="exact")
                .not_.is_("preferences", "null")
                .execute()
            )

            # Count user_preferences rows
            prefs_count = (
                self.client.table("user_preferences")
                .select("id", count="exact")
                .execute()
            )

            profiles_total = profiles_count.count
            prefs_total = prefs_count.count

            logger.info(
                f"Verification: {profiles_total} users with JSONB prefs, {prefs_total} rows in new table"
            )

            if prefs_total >= profiles_total:
                logger.info("✓ Verification passed: All users migrated")
                return True
            else:
                logger.warning(
                    f"⚠ Verification warning: {profiles_total - prefs_total} users not migrated"
                )
                return False

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

    def run(self):
        """Execute the full migration process."""
        logger.info("=" * 60)
        logger.info("USER PREFERENCES MIGRATION: JSONB → STRUCTURED TABLE")
        logger.info("=" * 60)

        try:
            # Fetch users
            logger.info("\nStep 1: Fetching users with JSONB preferences...")
            users = self.get_users_with_preferences()
            self.migration_stats["total_users"] = len(users)
            logger.info(f"Found {len(users)} users with preferences")

            # Migrate each user
            logger.info("\nStep 2: Migrating preferences...")
            for user_data in users:
                user_id = user_data["id"]
                prefs = user_data["preferences"]
                self.migrate_user(user_id, prefs)

            # Verify
            logger.info("\nStep 3: Verifying migration...")
            verification_passed = self.verify_migration()

            # Report
            logger.info("\n" + "=" * 60)
            logger.info("MIGRATION REPORT")
            logger.info("=" * 60)
            logger.info(f"Total users:     {self.migration_stats['total_users']}")
            logger.info(f"Migrated:        {self.migration_stats['migrated']}")
            logger.info(f"Skipped:         {self.migration_stats['skipped']}")
            logger.info(f"Errors:          {self.migration_stats['errors']}")
            logger.info(
                f"Verification:    {'✓ PASSED' if verification_passed else '✗ FAILED'}"
            )

            if self.migration_stats["error_details"]:
                logger.info("\nError Details:")
                for error in self.migration_stats["error_details"]:
                    logger.info(f"  - User {error['user_id']}: {error['error']}")

            logger.info("=" * 60)

            # Exit code
            if self.migration_stats["errors"] > 0 or not verification_passed:
                logger.error("\n⚠ Migration completed with errors or warnings")
                return 1
            else:
                logger.info("\n✓ Migration completed successfully!")
                return 0

        except Exception as e:
            logger.error(f"\n✗ Migration failed: {e}")
            return 1


def main():
    """Main entry point."""
    migrator = PreferencesMigrator()
    exit_code = migrator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
