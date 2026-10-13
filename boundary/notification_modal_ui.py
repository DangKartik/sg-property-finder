from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class NotificationModalUI:
    """«boundary»"""

    modalTitle: str
    modalMessage: str

    def showModal(self, title: str, message: str) -> None:
        raise NotImplementedError  # TODO

    def closeModal(self) -> None:
        raise NotImplementedError  # TODO
