"""
List all users and their roles.
Useful for managing your team.
"""

from services.supabase_client import get_supabase_admin_client


def list_users():
    print("=" * 60)
    print("ALL USERS")
    print("=" * 60)

    try:
        admin_client = get_supabase_admin_client()

        # Get all user profiles
        result = (
            admin_client.table("user_profiles")
            .select("*")
            .order("created_at")
            .execute()
        )

        if not result.data or len(result.data) == 0:
            print("\nNo users found.")
            return

        print(f"\nTotal users: {len(result.data)}\n")

        for i, user in enumerate(result.data, 1):
            print(f"{i}. {user['email']}")
            print(f"   Role: {user['role'].upper()}")
            print(f"   Name: {user.get('full_name', 'N/A')}")
            print(f"   Active: {'Yes' if user['is_active'] else 'No'}")
            print(f"   Created: {user['created_at'][:10]}")
            if user.get("last_login"):
                print(f"   Last Login: {user['last_login'][:10]}")
            print()

    except Exception as e:
        print(f"\n❌ Error: {e!s}")


if __name__ == "__main__":
    list_users()
