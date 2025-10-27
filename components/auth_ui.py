"""
Authentication UI components for Streamlit.
Provides login and signup forms with session management.
"""

import streamlit as st

from services.auth_service import AuthService
from utils.logger import Logger


logger = Logger(__name__)


def initialize_session_state():
    """Initialize session state variables for authentication."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "show_signup" not in st.session_state:
        st.session_state.show_signup = False


def render_login_form(auth_service: AuthService):
    """
    Render login form.

    Args:
        auth_service: AuthService instance
    """
    st.markdown("### 🔐 Login to Manuscript Alert System")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="your.email@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("Login", use_container_width=True)
        with col2:
            signup_button = st.form_submit_button("Sign Up Instead", use_container_width=True)

        if signup_button:
            st.session_state.show_signup = True
            st.rerun()

        if submit:
            if not email or not password:
                st.error("Please enter both email and password")
                return

            with st.spinner("Logging in..."):
                result = auth_service.login(email, password)

            if result["success"]:
                st.session_state.authenticated = True
                st.session_state.user = result["user"]
                logger.info(f"User logged in: {email}")
                st.success(f"Welcome back, {result['user']['email']}!")
                st.rerun()
            else:
                st.error(result["error"])
                logger.warning(f"Failed login attempt for: {email}")


def render_signup_form(auth_service: AuthService):
    """
    Render signup form.

    Args:
        auth_service: AuthService instance
    """
    st.markdown("### ✍️ Create New Account")

    with st.form("signup_form"):
        email = st.text_input(
            "Email *",
            placeholder="your.email@example.com",
            help="Required. This is your primary login identifier."
        )
        password = st.text_input(
            "Password *",
            type="password",
            placeholder="Choose a strong password"
        )
        password_confirm = st.text_input(
            "Confirm Password *",
            type="password",
            placeholder="Re-enter your password"
        )

        st.markdown("---")
        st.caption("Optional field:")

        full_name = st.text_input(
            "Full Name (optional)",
            placeholder="Your full name"
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("Create Account", use_container_width=True)
        with col2:
            login_button = st.form_submit_button("Back to Login", use_container_width=True)

        if login_button:
            st.session_state.show_signup = False
            st.rerun()

        if submit:
            # Validation
            if not email or not password:
                st.error("Email and password are required")
                return

            if "@" not in email:
                st.error("Please enter a valid email address")
                return

            if len(password) < 6:
                st.error("Password must be at least 6 characters")
                return

            if password != password_confirm:
                st.error("Passwords do not match")
                return

            with st.spinner("Creating account..."):
                result = auth_service.signup(
                    email=email,
                    password=password,
                    full_name=full_name if full_name else None
                )

            if result["success"]:
                st.session_state.authenticated = True
                st.session_state.user = result["user"]
                logger.info(f"New user registered: {email}")
                st.success(f"Account created successfully! Welcome, {email}!")
                st.rerun()
            else:
                st.error(result["error"])
                logger.warning(f"Failed signup attempt for: {email}")


def render_auth_page(auth_service: AuthService):
    """
    Render authentication page (login or signup).

    Args:
        auth_service: AuthService instance
    """
    initialize_session_state()

    # Center the auth form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("# 📚 Manuscript Alert System")
        st.markdown("---")

        if st.session_state.show_signup:
            render_signup_form(auth_service)
        else:
            render_login_form(auth_service)


def render_user_menu(auth_service: AuthService):
    """
    Render user menu in sidebar with logout option.

    Args:
        auth_service: AuthService instance
    """
    if not st.session_state.get("authenticated"):
        return

    user = st.session_state.get("user")
    if not user:
        return

    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### 👤 {user.get('full_name') or user['email']}")

        if user.get("full_name"):
            st.caption(user["email"])

        st.caption(f"Role: {user['role'].upper()}")

        if st.button("🚪 Logout", use_container_width=True):
            auth_service.logout()
            st.session_state.authenticated = False
            st.session_state.user = None
            logger.info(f"User logged out: {user['email']}")
            st.rerun()


def require_auth(auth_service: AuthService) -> bool:
    """
    Protect a page by requiring authentication.
    Call this at the start of your app.

    Args:
        auth_service: AuthService instance

    Returns:
        True if authenticated, False otherwise (shows login page)
    """
    initialize_session_state()

    # Check if already authenticated in session
    if st.session_state.get("authenticated"):
        return True

    # Try to restore session from Supabase
    current_user = auth_service.get_current_user()
    if current_user:
        st.session_state.authenticated = True
        st.session_state.user = current_user
        logger.info(f"Session restored for user: {current_user['username']}")
        return True

    # Not authenticated - show login page
    render_auth_page(auth_service)
    return False
