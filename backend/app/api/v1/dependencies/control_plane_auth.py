from __future__ import annotations

import hmac
import os
from dataclasses import dataclass

from fastapi import Header, HTTPException, status


CONTROL_PLANE_AUTH_TOKEN_ENV = "CORTAI_CONTROL_PLANE_TOKEN"
INTERNAL_CONTROL_PLANE_AUTH_TOKEN_ENV = "CORTAI_INTERNAL_CONTROL_PLANE_TOKEN"


@dataclass(frozen=True)
class ControlPlaneIdentity:
    subject: str
    scopes: tuple[str, ...]
    auth_method: str
    internal: bool = False


def _auth_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": message}},
        headers={"WWW-Authenticate": "Bearer"},
    )


def _required_configured_token(env_name: str) -> str:
    token = str(os.getenv(env_name) or "").strip()
    if not token:
        raise _auth_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "CONTROL_PLANE_AUTH_NOT_CONFIGURED",
            "control plane auth is not configured",
        )
    return token


def _extract_bearer_token(authorization: str | None) -> str:
    raw = str(authorization or "").strip()
    scheme, _, token = raw.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED,
            "CONTROL_PLANE_AUTH_REQUIRED",
            "control plane authentication is required",
        )
    return token.strip()


def _verify_static_bearer_token(
    *,
    authorization: str | None,
    env_name: str,
    subject: str,
    scopes: tuple[str, ...],
    internal: bool,
) -> ControlPlaneIdentity:
    expected = _required_configured_token(env_name)
    supplied = _extract_bearer_token(authorization)
    if not hmac.compare_digest(supplied, expected):
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED,
            "CONTROL_PLANE_AUTH_REQUIRED",
            "control plane authentication is required",
        )
    return ControlPlaneIdentity(
        subject=subject,
        scopes=scopes,
        auth_method="static_bearer_token",
        internal=internal,
    )


def require_control_plane_admin(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ControlPlaneIdentity:
    return _verify_static_bearer_token(
        authorization=authorization,
        env_name=CONTROL_PLANE_AUTH_TOKEN_ENV,
        subject="control-plane-admin",
        scopes=("ops:actions",),
        internal=False,
    )


def require_internal_control_plane(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ControlPlaneIdentity:
    return _verify_static_bearer_token(
        authorization=authorization,
        env_name=INTERNAL_CONTROL_PLANE_AUTH_TOKEN_ENV,
        subject="internal-control-plane",
        scopes=("internal:maestro",),
        internal=True,
    )
