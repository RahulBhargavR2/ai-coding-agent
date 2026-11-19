from dataclasses import dataclass

@dataclass(frozen=True)
class ChangeReviewerConfig:
    max_files: int = 20
    max_change_size: int = 100_000