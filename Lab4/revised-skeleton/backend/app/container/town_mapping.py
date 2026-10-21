from __future__ import annotations


class TownMapping:
    mapping: dict[str, str]

    def __init__(self, mapping: dict[str, str]) -> None: ...
    def resolveTown(self, planningAreaName: str) -> str | None: ...
