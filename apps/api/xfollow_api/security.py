from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, Request

from .config import load_runtime_config
from .models import UserContext


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "administrador": {"read", "edit", "validate", "export"},
    "admin": {"read", "edit", "validate", "export"},
    "responsable_contratacion": {"read", "edit", "validate", "export"},
    "responsable_contrato": {"read", "edit", "validate", "export"},
    "tecnico_promotor": {"read", "edit"},
    "editor": {"read", "edit"},
    "juridico": {"read", "edit", "validate", "export"},
    "intervencion": {"read", "validate", "export"},
    "revisor": {"read", "validate", "export"},
    "consulta": {"read"},
    "lector": {"read"},
}


def required_permission(request: Request) -> str:
    path = request.url.path
    if path.endswith("/export") or path.endswith("/export.zip"):
        return "export"
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return "read"
    if "/validate" in path or path.endswith("/resolve") or path.endswith("/apply"):
        return "validate"
    return "edit"


def permissions_for_roles(roles: list[str]) -> set[str]:
    return set().union(*(ROLE_PERMISSIONS.get(role, set()) for role in roles))


def has_permission(user: UserContext, permission: str) -> bool:
    return permission in permissions_for_roles(user.roles)


def ensure_permission(user: UserContext, permission: str) -> None:
    if not has_permission(user, permission):
        raise HTTPException(status_code=403, detail=f"permission_required:{permission}")


def current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None),
    x_roles: str | None = Header(default=None),
) -> UserContext:
    config = load_runtime_config()
    environment = config.app_env.strip().lower()
    local_environment = environment in {"local", "development", "dev", "test"}
    if config.auth_mode == "development_headers" and local_environment:
        user_id = x_user_id or "demo-user"
        tenant_id = x_tenant_id or "tenant-demo"
        role_header = x_roles or "responsable_contrato"
    elif config.auth_mode == "bearer":
        if not config.auth_bearer_token:
            raise HTTPException(status_code=503, detail="authentication_not_configured")
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not secrets.compare_digest(token, config.auth_bearer_token):
            raise HTTPException(status_code=401, detail="invalid_or_missing_bearer_token", headers={"WWW-Authenticate": "Bearer"})
        if not x_user_id or not x_tenant_id:
            raise HTTPException(status_code=401, detail="trusted_identity_headers_required")
        user_id = x_user_id
        tenant_id = x_tenant_id
        role_header = x_roles or "consulta"
    else:
        raise HTTPException(status_code=503, detail="insecure_or_unknown_auth_mode")

    roles = [role.strip().lower() for role in role_header.split(",") if role.strip()]
    permissions = permissions_for_roles(roles)
    required = required_permission(request)
    if required not in permissions:
        raise HTTPException(status_code=403, detail=f"permission_required:{required}")
    return UserContext(user_id=user_id, tenant_id=tenant_id, roles=roles)
