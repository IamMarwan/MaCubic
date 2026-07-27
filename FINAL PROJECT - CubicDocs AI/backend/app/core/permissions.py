from enum import StrEnum


class UserRole(StrEnum):
    ADMINISTRATOR = "administrator"
    DOCUMENT_CONTROLLER = "document_controller"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.VIEWER: 10,
    UserRole.REVIEWER: 20,
    UserRole.DOCUMENT_CONTROLLER: 30,
    UserRole.ADMINISTRATOR: 40,
}


def role_has_minimum_level(
    current_role: UserRole,
    required_role: UserRole,
) -> bool:
    return ROLE_HIERARCHY[current_role] >= ROLE_HIERARCHY[required_role]


def role_is_allowed(
    current_role: UserRole,
    allowed_roles: set[UserRole],
) -> bool:
    return current_role in allowed_roles