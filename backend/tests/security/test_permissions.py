from app.security.permissions import PermissionChecker
from app.tools.permissions import ToolPermission


def test_permission_is_allowed():
    checker = PermissionChecker(allowed_permissions={ToolPermission.READ})

    assert checker.is_allowed(ToolPermission.READ) is True


def test_permission_is_denied():
    checker = PermissionChecker(allowed_permissions={ToolPermission.READ})

    assert checker.is_allowed(ToolPermission.WRITE) is False


def test_multiple_permissions():
    checker = PermissionChecker(
        allowed_permissions={
            ToolPermission.READ,
            ToolPermission.GIT,
        }
    )

    assert checker.is_allowed(ToolPermission.READ) is True
    assert checker.is_allowed(ToolPermission.GIT) is True
    assert checker.is_allowed(ToolPermission.WRITE) is False
