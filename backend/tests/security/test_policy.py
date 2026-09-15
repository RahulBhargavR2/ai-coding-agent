from app.security.policy import (
    CODING_POLICY,
    READ_ONLY_POLICY,
)
from app.tools.permissions import ToolPermission


def test_read_only_policy():
    assert READ_ONLY_POLICY.allows(ToolPermission.READ)

    assert READ_ONLY_POLICY.allows(ToolPermission.GIT)

    assert not READ_ONLY_POLICY.allows(ToolPermission.WRITE)


def test_coding_policy():
    assert CODING_POLICY.allows(ToolPermission.READ)

    assert CODING_POLICY.allows(ToolPermission.GIT)

    assert CODING_POLICY.allows(ToolPermission.WRITE)

    assert not CODING_POLICY.allows(ToolPermission.EXECUTE)
