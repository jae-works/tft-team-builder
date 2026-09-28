"""Small shared helpers used only by concrete Flet UI boundaries."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def flet_module() -> Any:
    """Import Flet lazily so UI-independent tests do not require it at import time."""

    import flet as ft

    return ft


def event_handler(callback: Callable[..., Any], *args: Any) -> Callable[[Any], Any]:
    """Adapt a callback with bound arguments to a Flet event callback."""

    def handle(_event: Any) -> Any:
        return callback(*args)

    return handle


def text_value_handler(callback: Callable[[str], Any]) -> Callable[[Any], Any]:
    """Adapt a Flet value control event to a normalized string callback."""

    def handle(event: Any) -> Any:
        return callback(str(event.control.value or ""))

    return handle
