"""Planning-area to HDB-town mapping."""

from __future__ import annotations

import json
from pathlib import Path


class TownMapping:
    """Stereotype: Container. Resolves URA planning areas to HDB towns."""

    mapping: dict[str, str]

    def __init__(self, mapping: dict[str, str]) -> None:
        """Create the mapping from a dictionary."""
        self.mapping = {
            str(key).strip().upper(): str(value).strip().upper()
            for key, value in mapping.items()
            if key and value and not str(key).startswith("_")
        }

    @classmethod
    def fromFile(cls, path: Path | str) -> "TownMapping":
        """Load a JSON mapping file.

        Raises:
            FileNotFoundError: If the mapping file does not exist.
            ValueError: If the file is not a JSON object.
        """
        file_path = Path(path)
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Town mapping JSON must be an object")
        return cls(data)

    def resolveTown(self, planningAreaName: str) -> str | None:
        """Return the HDB town for a planning area, or None."""
        return self.mapping.get(planningAreaName.strip().upper())
