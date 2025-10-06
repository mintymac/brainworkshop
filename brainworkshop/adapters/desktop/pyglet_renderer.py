"""Pyglet implementation of the renderer port.

This adapter implements the IRenderer interface using Pyglet for desktop rendering.
"""
from __future__ import annotations

from typing import Tuple, Optional
import pyglet

from brainworkshop.ports.renderer import IRenderer


class PygletRenderer(IRenderer):
    """Pyglet-based renderer for visual stimuli.

    Implements rendering using Pyglet's sprite and shape APIs.

    Attributes:
        window: Pyglet window for rendering
        batch: Pyglet batch for efficient rendering
        field_size: Size of the playing field in pixels
        field_center_x: X coordinate of field center
        field_center_y: Y coordinate of field center
    """

    def __init__(
        self,
        window: pyglet.window.Window,
        field_size: int = 400,
        field_center_x: Optional[int] = None,
        field_center_y: Optional[int] = None
    ) -> None:
        """Initialize Pyglet renderer.

        Args:
            window: Pyglet window instance
            field_size: Size of playing field in pixels
            field_center_x: X coordinate of field center (defaults to window center)
            field_center_y: Y coordinate of field center (defaults to window center)
        """
        self.window = window
        self.batch = pyglet.graphics.Batch()
        self.field_size = field_size
        self.field_center_x = field_center_x or window.width // 2
        self.field_center_y = field_center_y or window.height // 2

        # Current visual elements (for clearing/hiding)
        self.current_square = None
        self.current_sprites = []
        self.current_labels = []

    def show_square(self, position: int, color: Tuple[int, int, int]) -> None:
        """Show visual square at grid position.

        Args:
            position: Grid position (0-8 for 3x3 grid)
            color: RGB color tuple (r, g, b) with values 0-255
        """
        # Calculate position in grid
        # Grid layout:
        # 0 1 2
        # 3 4 5
        # 6 7 8
        cell_size = self.field_size // 3
        square_size = int(cell_size * 0.9)  # 90% of cell for padding

        # Calculate center position
        col = (position + 1) % 3 - 1  # -1, 0, 1
        row = (position // 3 + 1) % 3 - 1  # -1, 0, 1

        center_x = self.field_center_x + col * cell_size
        center_y = self.field_center_y + row * cell_size

        # Create square (bottom-left corner position)
        x = center_x - square_size // 2
        y = center_y - square_size // 2

        # Use pyglet.shapes if available (Pyglet 1.4+)
        try:
            from pyglet import shapes
            self.current_square = shapes.Rectangle(
                x, y, square_size, square_size,
                color=color,
                batch=self.batch
            )
        except (ImportError, AttributeError):
            # Fallback to vertex lists for older Pyglet
            r, g, b = color
            self.current_square = self.batch.add(
                4, pyglet.gl.GL_QUADS, None,
                ('v2i', (x, y, x, y + square_size,
                        x + square_size, y + square_size,
                        x + square_size, y)),
                ('c3B', (r, g, b) * 4)
            )

    def show_text(self, text: str, x: int, y: int, size: int = 24) -> None:
        """Show text at specified position.

        Args:
            text: Text to display
            x: X coordinate
            y: Y coordinate
            size: Font size (default 24)
        """
        label = pyglet.text.Label(
            text,
            font_size=size,
            x=x, y=y,
            anchor_x='center',
            anchor_y='center',
            batch=self.batch
        )
        self.current_labels.append(label)

    def clear_display(self) -> None:
        """Clear all visual stimuli from display."""
        # Delete current square
        if self.current_square is not None:
            if hasattr(self.current_square, 'delete'):
                self.current_square.delete()
            self.current_square = None

        # Delete sprites
        for sprite in self.current_sprites:
            if hasattr(sprite, 'delete'):
                sprite.delete()
        self.current_sprites.clear()

        # Delete labels
        for label in self.current_labels:
            if hasattr(label, 'delete'):
                label.delete()
        self.current_labels.clear()

    def draw(self) -> None:
        """Render the current frame to the display."""
        self.batch.draw()

    def set_field_size(self, size: int) -> None:
        """Update field size.

        Args:
            size: New field size in pixels
        """
        self.field_size = size

    def set_field_center(self, x: int, y: int) -> None:
        """Update field center position.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.field_center_x = x
        self.field_center_y = y
