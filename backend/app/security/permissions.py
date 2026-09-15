from app.tools.permissions import ToolPermission

DEFAULT_ALLOWED_PERMISSIONS = {
    ToolPermission.READ,
    ToolPermission.GIT,
}

class PermissionChecker:
    def __init__(
        self,
        allowed_permissions: set[ToolPermission],
    ) -> None:
        self.allowed_permissions = allowed_permissions
    
    def is_allowed(self, permission: ToolPermission) -> bool:
        return permission in self.allowed_permissions
