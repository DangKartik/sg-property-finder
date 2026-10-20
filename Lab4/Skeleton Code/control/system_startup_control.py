from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Optional

if TYPE_CHECKING:
    from container.profile_catalog import ProfileCatalog
    from container.subzone_registry import SubzoneRegistry


class SystemStartupControl:
    """«control» Singleton start-up class that initialises the system on launch."""

    instance: ClassVar[Optional[SystemStartupControl]] = None  # private, static
    profileCatalog: ProfileCatalog  # private
    subzoneRegistry: SubzoneRegistry  # private

    def __init__(self, profileCatalog: ProfileCatalog, subzoneRegistry: SubzoneRegistry) -> None:
        """Create a SystemStartupControl with its attributes (TODO: add validation if needed)."""
        self.profileCatalog = profileCatalog
        self.subzoneRegistry = subzoneRegistry

    @staticmethod
    def getInstance() -> SystemStartupControl:
        """Get instance (public).

        Returns:
            SystemStartupControl
        """
        raise NotImplementedError  # TODO

    def main(self, args: list[str]) -> None:
        """Main (public).

        Args:
            args: list[str]
        """
        raise NotImplementedError  # TODO

    def initializeSystem(self) -> None:
        """Initialize system (public)."""
        raise NotImplementedError  # TODO
