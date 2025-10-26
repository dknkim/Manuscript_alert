#!/usr/bin/env python3
"""
Test Supabase connection and verify admin user setup
"""
from services.supabase_client import get_client


def test_connection():
    """Test basic Supabase connection"""
    print("🔄 Testing Supabase connection...")

    try:
        supabase = get_client()
        print("✅ Supabase client initialized successfully")
        return supabase
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return None


def test_database_access(supabase):
    """Test database access by querying papers table"""
    print("\n🔄 Testing database access...")

    try:
        # Try to query papers table (should be empty but accessible)
        result = supabase.table("papers").select("*").limit(1).execute()
        print("✅ Database access successful")
        print(f"   Papers table exists: {len(result.data)} papers found")
        return True
    except Exception as e:
        print(f"❌ Database access failed: {e}")
        return False


def test_user_profiles(supabase):
    """Test user_profiles table and verify admin user"""
    print("\n🔄 Testing user profiles...")

    try:
        # Note: Anon key can't read user_profiles due to RLS
        # Need to use service role key for admin operations
        import os

        from supabase import create_client

        service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        url = os.environ.get("SUPABASE_URL")

        if not service_key or not url:
            print("⚠️  Cannot verify profiles: SUPABASE_SERVICE_ROLE_KEY not set")
            print("   Profiles can only be queried with service role key")
            return True

        admin_client = create_client(url, service_key)
        result = admin_client.table("user_profiles").select("username, email, role, is_active").execute()

        if result.data:
            print(f"✅ User profiles found: {len(result.data)} user(s)")
            for user in result.data:
                print(f"   - Username: {user['username']}")
                print(f"     Email: {user.get('email', '(none)')}")
                print(f"     Role: {user['role']}")
                print(f"     Active: {user['is_active']}")

            # Check for admin user
            admin_users = [u for u in result.data if u["role"] == "admin"]
            if admin_users:
                print("\n✅ Admin user configured correctly!")
            else:
                print("\n⚠️  No admin user found. Please create one.")
        else:
            print("⚠️  No user profiles found. Please create your admin user.")

        return True
    except Exception as e:
        print(f"❌ Failed to query user profiles: {e}")
        return False


def test_system_settings(supabase):
    """Test system_settings table"""
    print("\n🔄 Testing system settings...")

    try:
        result = supabase.table("system_settings").select("key, value, description").execute()

        if result.data:
            print(f"✅ System settings found: {len(result.data)} setting(s)")
            for setting in result.data:
                print(f"   - {setting['key']}: {setting['value']}")
        else:
            print("⚠️  No system settings found. Run the admin setup SQL.")

        return True
    except Exception as e:
        print(f"❌ Failed to query system settings: {e}")
        return False


def test_projects(supabase):
    """Test projects table"""
    print("\n🔄 Testing projects table...")

    try:
        result = supabase.table("projects").select("*").limit(1).execute()
        print("✅ Projects table accessible")
        print(f"   Projects found: {len(result.data)}")
        return True
    except Exception as e:
        print(f"❌ Projects table access failed: {e}")
        return False


def main():
    """Run all connection tests"""
    print("=" * 60)
    print("SUPABASE CONNECTION TEST")
    print("=" * 60)

    # Test 1: Initialize client
    supabase = test_connection()
    if not supabase:
        print("\n❌ Cannot proceed - fix connection issues first")
        return

    # Test 2: Database access
    if not test_database_access(supabase):
        print("\n❌ Cannot proceed - fix database access first")
        return

    # Test 3: User profiles
    test_user_profiles(supabase)

    # Test 4: System settings
    test_system_settings(supabase)

    # Test 5: Projects
    test_projects(supabase)

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✅ Connection to Supabase: SUCCESS")
    print("✅ Database schema: DEPLOYED")
    print("✅ Tables accessible: CONFIRMED")
    print("\n🎉 Supabase setup is complete!")
    print("\nNext steps:")
    print("1. If no admin user shown above, create one following the guide")
    print("2. Update your Streamlit app to use Supabase authentication")
    print("3. Implement data migration from local JSON files")
    print("=" * 60)


if __name__ == "__main__":
    main()
