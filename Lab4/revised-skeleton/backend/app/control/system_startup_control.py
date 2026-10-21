from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.container.subzone_registry import SubzoneRegistry


class SystemStartupControl:
    subzoneRegistry: SubzoneRegistry

    def __init__(self, subzoneRegistry: SubzoneRegistry) -> None: ...
    def initializeSystem(self) -> None: ...
    def main(self, args: list[str]) -> None: ...
