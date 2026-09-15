from enum import StrEnum


class ToolPermission(StrEnum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    GIT = "git"
