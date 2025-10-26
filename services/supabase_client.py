"""
Supabase client initialization and configuration
"""

import os

from dotenv import load_dotenv

from supabase import Client, create_client


# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client

    Returns:
        Client: Authenticated Supabase client

    Raises:
        ValueError: If Supabase credentials are missing
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError(
            "Missing Supabase credentials. Please set SUPABASE_URL and "
            "SUPABASE_ANON_KEY in your .env file"
        )

    return create_client(url, key)


def get_supabase_admin_client() -> Client:
    """
    Initialize and return Supabase client with service role (admin access)

    Use this for background jobs and admin operations

    Returns:
        Client: Admin Supabase client with elevated permissions

    Raises:
        ValueError: If service role key is missing
    """
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not service_key:
        raise ValueError(
            "Missing Supabase service role credentials. Please set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in your .env file"
        )

    return create_client(url, service_key)


# Singleton instance for regular client
_supabase_client = None


def get_client() -> Client:
    """
    Get or create singleton Supabase client instance

    Returns:
        Client: Cached Supabase client
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client
