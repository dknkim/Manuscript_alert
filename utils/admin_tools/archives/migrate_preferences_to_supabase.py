#!/usr/bin/env python3
"""
Populate user preferences from config/settings.py to Supabase user_profiles.preferences

This script populates preferences for existing users who don't have them yet.
New users automatically get preferences on signup.
"""

import os
import sys


# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config import settings
from services.supabase_client import get_supabase_admin_client


def populate_user_preferences(user_email: str):
    """
    Populate preferences from settings.py to a specific user's profile.
    Only updates if preferences are missing or minimal.

    Args:
        user_email: Email of the user to populate preferences for
    """
    print(f"\n{'='*60}")
    print("MIGRATE PREFERENCES TO SUPABASE")
    print(f"{'='*60}\n")

    admin_client = get_supabase_admin_client()

    # Find user by email
    print(f"Looking up user: {user_email}")
    result = admin_client.table("user_profiles")\
        .select("*")\
        .eq("email", user_email)\
        .single()\
        .execute()

    if not result.data:
        print(f"❌ User not found: {user_email}")
        return False

    user = result.data
    print(f"✅ Found user: {user['full_name'] or user['email']}")
    print(f"   Role: {user['role']}")
    print(f"   Current preferences: {len(user.get('preferences', {}))} keys")

    # Build comprehensive preferences from settings.py
    preferences = {
        # Basic UI preferences
        "theme": settings.UI_SETTINGS.get("theme", "light"),
        "notifications_enabled": True,
        "email_alerts": False,

        # Keywords
        "keywords": settings.DEFAULT_KEYWORDS,

        # Journal settings
        "target_journals": settings.TARGET_JOURNALS,
        "journal_exclusions": settings.JOURNAL_EXCLUSIONS,
        "journal_scoring": settings.JOURNAL_SCORING,

        # Keyword scoring
        "keyword_scoring": settings.KEYWORD_SCORING,

        # Search settings
        "search_settings": settings.DEFAULT_SEARCH_SETTINGS,

        # UI settings
        "ui_settings": settings.UI_SETTINGS,
    }

    print("\n📦 Migration package:")
    print(f"   - Keywords: {len(preferences['keywords'])} items")
    print(f"   - Target journals: {len(preferences['target_journals']['exact_matches'])} exact matches")
    print(f"   - Journal exclusions: {len(preferences['journal_exclusions'])} patterns")
    print(f"   - Search settings: {len(preferences['search_settings'])} settings")

    # Ask for confirmation
    print(f"\n⚠️  This will OVERWRITE existing preferences for {user_email}")
    confirm = input("Continue? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("❌ Migration cancelled")
        return False

    # Update user profile with new preferences
    print("\n📝 Updating user profile...")
    update_result = admin_client.table("user_profiles")\
        .update({
            "preferences": preferences,
            "updated_at": "now()"
        })\
        .eq("id", user["id"])\
        .execute()

    if update_result.data:
        print("✅ Preferences migrated successfully!")
        print("\n📊 Summary:")
        print(f"   - User: {user['email']}")
        print(f"   - Total preference keys: {len(preferences)}")
        print(f"   - Keywords: {len(preferences['keywords'])}")
        print("   - Settings stored in Supabase")
        return True
    else:
        print("❌ Failed to update preferences")
        return False


def migrate_all_users():
    """Migrate preferences to all users in the system."""
    print(f"\n{'='*60}")
    print("MIGRATE PREFERENCES TO ALL USERS")
    print(f"{'='*60}\n")

    admin_client = get_supabase_admin_client()

    # Fetch all users
    result = admin_client.table("user_profiles")\
        .select("email")\
        .execute()

    if not result.data:
        print("❌ No users found")
        return

    users = result.data
    print(f"Found {len(users)} users")
    print("\nUsers:")
    for i, user in enumerate(users, 1):
        print(f"  {i}. {user['email']}")

    print(f"\n⚠️  This will OVERWRITE preferences for ALL {len(users)} users")
    confirm = input("Continue? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("❌ Migration cancelled")
        return

    success_count = 0
    fail_count = 0

    for user in users:
        print(f"\n{'─'*60}")
        if populate_user_preferences(user["email"]):
            success_count += 1
        else:
            fail_count += 1

    print(f"\n{'='*60}")
    print("MIGRATION COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {fail_count}")


def main():
    """Main entry point."""
    print("\nMIGRATE USER PREFERENCES TO SUPABASE")
    print("="*60)
    print("\nOptions:")
    print("  1. Migrate specific user")
    print("  2. Migrate all users")
    print("  3. Cancel")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        email = input("\nEnter user email: ").strip()
        if email:
            populate_user_preferences(email)
        else:
            print("❌ Email required")
    elif choice == "2":
        migrate_all_users()
    else:
        print("❌ Cancelled")


if __name__ == "__main__":
    main()
