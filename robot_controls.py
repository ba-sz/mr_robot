"""Skróty klawiszowe gry. Same przypisania łatwo pokazać na lekcji Python."""

from collections.abc import Callable
import tkinter as tk


KEY_ACTIONS: dict[str, str] = {
    "Up": "góra",
    "Down": "dół",
    "Left": "lewo",
    "Right": "prawo",
    "s": "start",
    "n": "nowa runda",
    "t": "turbo",
    "l": "ultra",
    "p": "przygoda",
    "e": "popraw strzałki",
    "u": "cofnij",
    "r": "wyczyść",
}


def dispatch_key(keysym: str, handler: Callable[[str], None]) -> bool:
    """Przekaż rozpoznany skrót głównemu kontrolerowi gry."""
    action = KEY_ACTIONS.get(keysym)
    if action is None:
        action = KEY_ACTIONS.get(keysym.casefold())
    if action is None:
        return False
    handler(keysym)
    return True


def bind_keyboard(root: tk.Misc, handler: Callable[[str], None]) -> None:
    """Obsługuj skróty niezależnie od tego, który przycisk ma fokus."""
    root.bind("<KeyPress>", lambda event: dispatch_key(event.keysym, handler))
