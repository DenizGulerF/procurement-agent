"""
Authorization helpers.

For the MVP, authorization is based on a demo `acting_user_id` passed in requests.
The logic itself is real and testable — roles are enforced in application code,
never delegated to the LLM.
"""

from fastapi import HTTPException

from app.models.models import User, UserRole


def require_role(user: User, *allowed_roles: UserRole) -> None:
    """Raise 403 if user does not have one of the allowed roles."""
    if user.role not in allowed_roles:
        allowed = ", ".join(r.value for r in allowed_roles)
        raise HTTPException(
            status_code=403,
            detail=f"Action requires one of [{allowed}]. User '{user.name}' has role {user.role.value}.",
        )


def can_create_procurement(user: User) -> bool:
    return user.role in (UserRole.EMPLOYEE, UserRole.PROCUREMENT, UserRole.MANAGER)


def can_approve_procurement(user: User) -> bool:
    return user.role == UserRole.MANAGER


def can_view_procurement(user: User) -> bool:
    return user.role in (UserRole.PROCUREMENT, UserRole.MANAGER, UserRole.EMPLOYEE)
