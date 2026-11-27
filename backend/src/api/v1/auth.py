"""Session-cookie auth endpoints for the Vite SPA frontend."""

from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from src.api.auth import (
    SESSION_COOKIE,
    SESSION_DURATION_SEC,
    _decode_session,
    _get_signing_key,
    sign_session_token,
)
from src.api.deps import get_user_store
from src.api.v1.contracts import AuthMeResponse, AuthResponse, LoginRequest, LogoutResponse
from src.core.foundation.auth.passwords import hash_password, verify_password
from src.core.config import get_config
from src.ports.users import UserAlreadyExistsError, UserRecord, UserStore
from src.utils.exceptions import PersistenceUnavailableError

router = APIRouter()


def _public_account_response(*, authenticated: bool = False, username: str | None = None) -> AuthMeResponse:
    """Return the public account API response."""
    return AuthMeResponse(
        authenticated=authenticated,
        account_type="public",
        user_id=None,
        username=username,
        display_name="Public account",
    )


def _user_account_response(user: UserRecord) -> AuthMeResponse:
    """Return a user account API response."""
    return AuthMeResponse(
        authenticated=True,
        account_type="user",
        user_id=user.user_id,
        username=user.username,
        display_name=user.display_name,
    )


def _set_session_cookie(response: Response, token: str) -> None:
    """Attach the signed session cookie to a response."""
    cfg = get_config()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=cfg.is_production,
        max_age=SESSION_DURATION_SEC,
        path="/",
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    response: Response,
    user_store: UserStore = Depends(get_user_store),
) -> AuthResponse:
    """Login with username/password, creating the user when missing.

    Username + password uses persisted ``users`` rows. If the username does
    not exist, a new active user is created and signed in. Password-only login
    keeps the legacy API-key session behavior for existing deployments/tests.
    """
    cfg = get_config()

    if not body.password:
        raise HTTPException(status_code=400, detail="Password is required")

    signing_key = _get_signing_key()
    if body.username is None:
        secret = cfg.api_key
        if not secret:
            raise HTTPException(status_code=500, detail="Authentication not configured")
        if not hmac.compare_digest(body.password, secret):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = sign_session_token(signing_key)
        _set_session_cookie(response, token)
        return AuthResponse(success=True, account=_public_account_response(authenticated=True))

    user = await user_store.get_by_username(body.username)
    if user is not None:
        if user.status != "active" or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = sign_session_token(signing_key, user_id=user.user_id, username=user.username)
        _set_session_cookie(response, token)
        return AuthResponse(success=True, account=_user_account_response(user))

    try:
        user = await user_store.create(
            username=body.username,
            password_hash=hash_password(body.password),
            display_name=body.username,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=401, detail="Invalid credentials") from exc

    token = sign_session_token(signing_key, user_id=user.user_id, username=user.username)
    _set_session_cookie(response, token)
    return AuthResponse(success=True, account=_user_account_response(user))


@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response) -> LogoutResponse:
    """Delete the session cookie.

    Args:
        response: The outgoing response, used to delete the cookie.

    Returns:
        LogoutResponse with ``success=True``.
    """
    response.delete_cookie(key=SESSION_COOKIE, path="/")
    return LogoutResponse(success=True)


@router.get("/me", response_model=AuthMeResponse)
async def me(
    request: Request,
    user_store: UserStore = Depends(get_user_store),
) -> AuthMeResponse:
    """Return the current session account, defaulting to public."""
    signing_key = _get_signing_key()
    token = request.cookies.get(SESSION_COOKIE)

    claims = _decode_session(token, signing_key) if token else None
    if claims is None:
        return _public_account_response(authenticated=False)

    if claims.user_id is None:
        return _public_account_response(authenticated=True, username=claims.username)

    try:
        user = await user_store.get_by_id(claims.user_id)
    except (RuntimeError, PersistenceUnavailableError):
        return _public_account_response(authenticated=False)

    if user is None or user.status != "active":
        return _public_account_response(authenticated=False)

    return _user_account_response(user)
