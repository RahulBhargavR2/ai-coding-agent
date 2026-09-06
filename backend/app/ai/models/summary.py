from dataclasses import dataclass


@dataclass(frozen=True)
class SummaryResult:
    summary: str
