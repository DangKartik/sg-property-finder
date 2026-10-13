from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.container.profile_catalog import ProfileCatalog
    from sgpropfinder.container.subzone_registry import SubzoneRegistry


class SystemStartupControl:
    """«control»"""

    profileCatalog: ProfileCatalog
    subzoneRegistry: SubzoneRegistry

    def main(self, args: list[str]) -> None:
        raise NotImplementedError  # TODO

    def initializeSystem(self) -> None:
        raise NotImplementedError  # TODO

    def launchUI(self) -> None:
        raise NotImplementedError  # TODO
