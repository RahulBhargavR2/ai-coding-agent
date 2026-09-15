from dataclasses import dataclass

from app.tools.permissions import ToolPermission


@dataclass(frozen=True)
class ExecutionPolicy:
    allowed_permissions: frozenset[ToolPermission]

    def allows(self, permission: ToolPermission) -> bool:
        return permission in self.allowed_permissions


READ_ONLY_POLICY = ExecutionPolicy(
    allowed_permissions=frozenset(
        {
            ToolPermission.READ,
            ToolPermission.GIT,
        }
    )
)


CODING_POLICY = ExecutionPolicy(
    allowed_permissions=frozenset(
        {
            ToolPermission.READ,
            ToolPermission.GIT,
            ToolPermission.WRITE,
        }
    )
)
