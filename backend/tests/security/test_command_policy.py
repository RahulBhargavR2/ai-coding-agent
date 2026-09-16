from app.security.command_policy import (
    CommandPolicy,
    DEFAULT_COMMAND_POLICY,
)


def test_command_policy_allows_allowed_command():
    policy = CommandPolicy(
        allowed_commands=frozenset({"pytest"}),
    )

    assert policy.allows(["pytest", "-q"]) is True


def test_command_policy_rejects_unknown_command():
    policy = CommandPolicy(
        allowed_commands=frozenset({"pytest"}),
    )

    assert policy.allows(["rm", "-rf", "."]) is False


def test_command_policy_rejects_empty_command():
    policy = CommandPolicy(
        allowed_commands=frozenset({"pytest"}),
    )

    assert policy.allows([]) is False


def test_default_command_policy_allows_pytest():
    assert (
        DEFAULT_COMMAND_POLICY.allows(
            ["pytest", "-q"],
        )
        is True
    )
