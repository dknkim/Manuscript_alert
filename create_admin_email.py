"""
Create admin user with email-based authentication.
Run this after deploying the new email-based schema.
"""

from services.supabase_client import get_supabase_admin_client, get_supabase_client


def create_admin():
    print("=" * 60)
    print("CREATE ADMIN USER (Email-Based)")
    print("=" * 60)

    # Get inputs
    email = input("\nEnter admin email: ")
    password = input("Enter admin password: ")
    full_name = input("Enter full name (optional): ") or None

    try:
        # Initialize clients
        supabase = get_supabase_client()
        admin_client = get_supabase_admin_client()

        print("\n🔄 Creating auth user...")

        # Create auth user with auto-confirm
        # Note: We use admin client to bypass email confirmation
        try:
            auth_response = admin_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True  # Auto-confirm the user
            })
        except Exception as e:
            if "already been registered" in str(e):
                print("⚠️  User already exists in auth. Looking up existing user...")
                # Find existing user
                users = admin_client.auth.admin.list_users()
                auth_response = None
                for user in users:
                    if user.email == email:
                        auth_response = type("obj", (object,), {"user": user})()
                        break
                if not auth_response:
                    print("❌ Could not find existing user")
                    return
            else:
                raise

        if not auth_response.user:
            print("❌ Failed to create auth user")
            return

        user_id = auth_response.user.id
        print(f"✅ Auth user created with ID: {user_id}")

        print("\n🔄 Creating admin profile...")

        # Create admin profile
        profile_data = {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "role": "admin",  # ADMIN role
            "is_active": True
        }

        profile_result = admin_client.table("user_profiles")\
            .insert(profile_data)\
            .execute()

        if profile_result.data:
            print("✅ Admin profile created successfully!")
            print("\n" + "=" * 60)
            print("ADMIN USER CREATED!")
            print("=" * 60)
            print(f"Email: {email}")
            print("Role: admin")
            if full_name:
                print(f"Name: {full_name}")
            print("\nYou can now login to the app with this email and password.")
        else:
            print("❌ Failed to create profile")

    except Exception as e:
        print(f"\n❌ Error: {e!s}")

if __name__ == "__main__":
    create_admin()
