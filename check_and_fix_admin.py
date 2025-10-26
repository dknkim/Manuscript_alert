#!/usr/bin/env python3
"""
Check existing auth users and fix admin profile
"""
import os

from dotenv import load_dotenv

from supabase import create_client


load_dotenv()


def check_and_fix():
    """Check what exists and fix admin profile"""
    print("=" * 60)
    print("CHECKING EXISTING USERS")
    print("=" * 60)
    print()

    # Get Supabase client
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not service_key:
        print("❌ Missing credentials in .env")
        return

    supabase = create_client(url, service_key)

    try:
        # Check auth users
        print("1️⃣  Checking auth.users...")
        auth_users = supabase.auth.admin.list_users()

        if not auth_users:
            print("   No auth users found")
            return

        print(f"   Found {len(auth_users)} auth user(s):")
        for user in auth_users:
            print(f"   - Email: {user.email}")
            print(f"     UUID: {user.id}")
            print()

        # Check user_profiles
        print("2️⃣  Checking user_profiles...")
        profiles = supabase.table("user_profiles").select("*").execute()

        if profiles.data:
            print(f"   Found {len(profiles.data)} profile(s):")
            for profile in profiles.data:
                print(f"   - Username: {profile['username']}")
                print(f"     Email: {profile.get('email', '(none)')}")
                print(f"     Role: {profile['role']}")
                print(f"     UUID: {profile['id']}")
                print()
        else:
            print("   No profiles found")
            print()

        # Find auth users without profiles
        print("3️⃣  Looking for auth users without profiles...")
        auth_ids = {user.id for user in auth_users}
        profile_ids = {profile["id"] for profile in profiles.data} if profiles.data else set()
        missing_profiles = auth_ids - profile_ids

        if missing_profiles:
            print(f"   Found {len(missing_profiles)} auth user(s) without profile:")
            for user_id in missing_profiles:
                user = next(u for u in auth_users if u.id == user_id)
                print(f"   - Email: {user.email}")
                print(f"     UUID: {user_id}")
                print()

                # Ask to create profile
                create = input(f"   Create admin profile for {user.email}? (y/n): ").strip().lower()
                if create == "y":
                    username = input("   Username: ").strip() or "admin"
                    full_name = input("   Full name: ").strip() or "Admin User"

                    profile_data = {
                        "id": user_id,
                        "username": username,
                        "email": user.email,
                        "full_name": full_name,
                        "role": "admin",
                        "is_active": True
                    }

                    result = supabase.table("user_profiles").insert(profile_data).execute()

                    if result.data:
                        print()
                        print("   ✅ Admin profile created!")
                        print(f"   Username: {username}")
                        print("   Role: admin")
                    else:
                        print("   ❌ Failed to create profile")
        else:
            print("   All auth users have profiles ✅")

        # Check for admin users
        print()
        print("4️⃣  Checking for admin users...")
        admins = [p for p in (profiles.data or []) if p.get("role") == "admin"]

        if admins:
            print(f"   ✅ Found {len(admins)} admin(s):")
            for admin in admins:
                print(f"   - Username: {admin['username']}")
                print(f"     Email: {admin.get('email', '(none)')}")
        else:
            print("   ⚠️  No admin users found!")
            print("   You should create one.")

        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Auth users: {len(auth_users)}")
        print(f"User profiles: {len(profiles.data) if profiles.data else 0}")
        print(f"Admin users: {len(admins)}")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_and_fix()
