"""Clerk JWT verification — FastAPI dependency for authenticated routes."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWKClientError

from backend.src.config import get_app_config


_jwks_client: PyJWKClient | None = None
_jwks_client_url: str = ""

bearer = HTTPBearer(auto_error=False)


def _get_jwks_client() -> PyJWKClient | None:
    """Return a cached PyJWKClient, or None if CLERK_JWKS_URL is not set."""
    global _jwks_client, _jwks_client_url
    url = get_app_config().clerk_jwks_url
    if not url:
        return None
    if _jwks_client is None or _jwks_client_url != url:
        _jwks_client = PyJWKClient(url, cache_keys=True)
        _jwks_client_url = url
    return _jwks_client


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str | None:
    """
    Verify a Clerk JWT and return the Clerk user ID (the ``sub`` claim).

    Behaviour:
    - ``CLERK_JWKS_URL`` **not set** → returns ``None`` (local dev bypass, all requests allowed).
    - ``CLERK_JWKS_URL`` **set**, no token supplied → 401.
    - Invalid or expired token → 401.
    """
    client = _get_jwks_client()
    if client is None:
        return None  # Auth not configured — allow all (local dev)

    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk doesn't set aud by default
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")

        # Ensure the user row exists — required by FK constraints on settings/papers/model_presets.
        # Clerk includes the email in the JWT; fall back to a unique placeholder if absent.
        from backend.src.db import models as db_models
        from backend.src.db.neon import get_pool

        pool = get_pool()
        if pool is not None:
            email: str = payload.get("email") or f"{user_id}@clerk"
            await db_models.get_or_create_user(pool, user_id, email)

        return user_id
    except PyJWKClientError as exc:
        raise HTTPException(status_code=401, detail=f"JWKS error: {exc}") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc


# Convenience type alias — use as a route parameter type
CurrentUser = Annotated[str | None, Depends(get_current_user_id)]
