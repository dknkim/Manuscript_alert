"""
Promote an existing user to admin role.
Use this if your co-author already registered as regular user.
"""

from services.supabase_client import get_supabase_admin_client


def promote_to_admin():
    print("=" * 60)
    print("PROMOTE USER TO ADMIN")
    print("=" * 60)

    email = input("\nEnter email of user to promote: ")

    try:
        admin_client = get_supabase_admin_client()

        print("\n🔄 Looking up user...")

        # Find user by email
        result = (
            admin_client.table("user_profiles").select("*").eq("email", email).execute()
        )

        if not result.data or len(result.data) == 0:
            print(f"❌ No user found with email: {email}")
            print("\nUse create_new_admin.py to create a new admin user.")
            return

        user = result.data[0]
        print(f"✅ Found user: {user['email']}")
        print(f"   Current role: {user['role']}")
        print(f"   Name: {user.get('full_name', 'N/A')}")

        if user["role"] == "admin":
            print("\n⚠️  User is already an admin!")
            return

        print("\n🔄 Promoting to admin...")
        confirm = input("Confirm promotion? (yes/no): ")

        if confirm.lower() != "yes":
            print("Cancelled.")
            return

        # Update role to admin
        update_result = (
            admin_client.table("user_profiles")
            .update({"role": "admin"})
            .eq("id", user["id"])
            .execute()
        )

        if update_result.data:
            print("\n" + "=" * 60)
            print("USER PROMOTED TO ADMIN!")
            print("=" * 60)
            print(f"Email: {email}")
            print("New Role: admin")
            print("\nThey now have full admin privileges.")
        else:
            print("❌ Failed to update role")

    except Exception as e:
        print(f"\n❌ Error: {e!s}")


if __name__ == "__main__":
    promote_to_admin()
