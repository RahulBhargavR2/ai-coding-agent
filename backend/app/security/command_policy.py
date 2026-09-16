from dataclasses import dataclass


@dataclass(frozen=True)
class CommandPolicy:
    allowed_commands: frozenset[str]

    def allows(self, command: list[str]) -> bool:
        if not command:
            return False

        executable = command[0]

        return executable in self.allowed_commands

DEFAULT_COMMAND_POLICY = CommandPolicy(
    allowed_commands=frozenset(
        {
            "pytest",
            "python",
            "python3",
        }
    )
)
