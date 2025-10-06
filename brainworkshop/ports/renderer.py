"""Renderer port interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple


class IRenderer(ABC):
    """Interface for rendering stimuli to any display.

    This port defines the contract for visual rendering, allowing
    the domain logic to be independent of the specific rendering
    technology (Pyglet, web canvas, etc.).
    """

    @abstractmethod
    def show_square(self, position: int, color: Tuple[int, int, int]) -> None:
        """Show visual square at grid position.

        Args:
            position: Grid position (0-8 for 3x3 grid)
            color: RGB color tuple (r, g, b) with values 0-255
        """
        pass

    @abstractmethod
    def show_text(self, text: str, x: int, y: int, size: int = 24) -> None:
        """Show text at specified position.

        Args:
            text: Text to display
            x: X coordinate
            y: Y coordinate
            size: Font size (default 24)
        """
        pass

    @abstractmethod
    def clear_display(self) -> None:
        """Clear all visual stimuli from display."""
        pass

    @abstractmethod
    def draw(self) -> None:
        """Render the current frame to the display."""
        pass
