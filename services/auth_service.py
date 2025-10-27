"""
Authentication service for Manuscript Alert System.
Handles user login, signup, and session management with Supabase.
"""

from typing import Any

from supabase import Client
from utils.logger import Logger


logger = Logger(__name__)


class AuthService:
    """Manages user authentication and session state."""

    def __init__(self, supabase_client: Client):
        """
        Initialize authentication service.

        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client
        logger.info("AuthService initialized")

    def login(self, email: str, password: str) -> dict[str, Any]:
        """
        Login user with email and password.

        Args:
            email: User's email address
            password: User's password

        Returns:
            Dict with 'success' (bool), 'user' (dict), 'error' (str)
        """
        try:
            logger.info(f"Login attempt for email: {email}")

            # Authenticate with Supabase Auth
            auth_response = self.supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if auth_response.user:
                logger.info(f"User {email} logged in successfully")

                # Get user profile using admin client
                from services.supabase_client import get_supabase_admin_client

                admin_client = get_supabase_admin_client()

                # Update last_login and get profile
                admin_client.table("user_profiles").update({"last_login": "now()"}).eq(
                    "id", auth_response.user.id
                ).execute()

                profile = (
                    admin_client.table("user_profiles")
                    .select("id, email, role, full_name, is_active")
                    .eq("id", auth_response.user.id)
                    .single()
                    .execute()
                )

                if profile.data:
                    return {
                        "success": True,
                        "user": {
                            "id": profile.data["id"],
                            "email": profile.data["email"],
                            "role": profile.data["role"],
                            "full_name": profile.data.get("full_name"),
                        },
                        "session": auth_response.session,
                    }

            logger.warning(f"Authentication failed for email: {email}")
            return {"success": False, "error": "Invalid email or password"}

        except Exception as e:
            logger.error(f"Login error for {email}: {e!s}")
            return {"success": False, "error": "Invalid email or password"}

    def signup(
        self, email: str, password: str, full_name: str | None = None
    ) -> dict[str, Any]:
        """
        Register a new user.

        Args:
            email: Email address (required, primary login)
            password: Password (required)
            full_name: User's full name (optional)

        Returns:
            Dict with 'success' (bool), 'user' (dict), 'error' (str)
        """
        try:
            logger.info(f"Signup attempt for email: {email}")

            # Create auth user
            auth_response = self.supabase.auth.sign_up(
                {"email": email, "password": password}
            )

            if not auth_response.user:
                logger.error(f"Failed to create auth user for {email}")
                return {"success": False, "error": "Failed to create account"}

            # Create user profile using admin client
            # Note: Preferences are auto-created by trigger in user_preferences table
            from services.supabase_client import get_supabase_admin_client

            admin_client = get_supabase_admin_client()

            profile_data = {
                "id": auth_response.user.id,
                "email": email,
                "full_name": full_name,
                "role": "user",  # Default role
                "is_active": True,
            }

            profile_result = (
                admin_client.table("user_profiles").insert(profile_data).execute()
            )

            if profile_result.data:
                logger.info(f"User {email} registered successfully")
                return {
                    "success": True,
                    "user": {
                        "id": auth_response.user.id,
                        "email": email,
                        "role": "user",
                        "full_name": full_name,
                    },
                    "session": auth_response.session,
                }
            else:
                logger.error(f"Failed to create profile for {email}")
                return {"success": False, "error": "Failed to create user profile"}

        except Exception as e:
            logger.error(f"Signup error for {email}: {e!s}")
            return {"success": False, "error": f"Registration failed: {e!s}"}

    def logout(self) -> dict[str, Any]:
        """
        Logout current user.

        Returns:
            Dict with 'success' (bool), 'error' (str)
        """
        try:
            self.supabase.auth.sign_out()
            logger.info("User logged out successfully")
            return {"success": True}
        except Exception as e:
            logger.error(f"Logout error: {e!s}")
            return {"success": False, "error": "Logout failed"}

    def get_current_user(self) -> dict[str, Any] | None:
        """
        Get current authenticated user from session.

        Returns:
            User dict if authenticated, None otherwise
        """
        try:
            user = self.supabase.auth.get_user()
            if user:
                # Fetch profile info using admin client (RLS bypass)
                from services.supabase_client import get_supabase_admin_client

                admin_client = get_supabase_admin_client()

                profile = (
                    admin_client.table("user_profiles")
                    .select("email, role, full_name")
                    .eq("id", user.user.id)
                    .single()
                    .execute()
                )

                if profile.data:
                    return {"id": user.user.id, **profile.data}
            return None
        except Exception as e:
            logger.debug(f"No authenticated user: {e!s}")
            return None

    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self.get_current_user() is not None
