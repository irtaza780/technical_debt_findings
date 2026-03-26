import logging
import pygame
from typing import Optional
from constants import (
    INPUT_BG_COLOR,
    INPUT_BORDER_COLOR,
    INPUT_ACTIVE_BORDER_COLOR,
    TEXT_COLOR,
)

logger = logging.getLogger(__name__)

# UI Constants
CURSOR_BLINK_INTERVAL_MS = 500
TEXT_PADDING_X = 8
TEXT_PADDING_Y = 6
BORDER_WIDTH = 2
CURSOR_WIDTH = 2
PLACEHOLDER_COLOR = (150, 150, 150)


class InputBox:
    """
    A text input box widget for Pygame that handles keyboard input and rendering.
    
    Supports text entry, backspace deletion, and submission via Enter key.
    Displays a placeholder when empty and inactive, and shows a cursor when active.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        font: pygame.font.Font,
        placeholder: str = "",
    ) -> None:
        """
        Initialize the input box.
        
        Args:
            x: X coordinate of the top-left corner
            y: Y coordinate of the top-left corner
            width: Width of the input box
            height: Height of the input box
            font: Pygame font object for rendering text
            placeholder: Text to display when input is empty and inactive
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self._cursor_visible = True
        self._cursor_timer = 0

    def handle_event(self, event: pygame.event.EventType) -> Optional[str]:
        """
        Process input events (mouse clicks and keyboard input).
        
        Args:
            event: Pygame event object
            
        Returns:
            The submitted text if Enter was pressed, None otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle active state based on whether click is within box bounds
            self.active = self.rect.collidepoint(event.pos)
            return None

        if event.type == pygame.KEYDOWN and self.active:
            return self._handle_key_press(event)

        return None

    def _handle_key_press(self, event: pygame.event.EventType) -> Optional[str]:
        """
        Handle keyboard input when the input box is active.
        
        Args:
            event: Pygame KEYDOWN event
            
        Returns:
            The submitted text if Enter was pressed, None otherwise
        """
        if event.key == pygame.K_RETURN:
            # Submit text and clear for next input
            submitted_text = self.text
            self.text = ""
            return submitted_text

        if event.key == pygame.K_BACKSPACE:
            # Remove last character
            self.text = self.text[:-1]
            return None

        if event.key == pygame.K_ESCAPE:
            # Deactivate input box without submission
            self.active = False
            return None

        # Add printable characters to text
        if event.unicode and event.unicode.isprintable():
            self.text += event.unicode

        return None

    def draw(self, surface: pygame.Surface) -> None:
        """
        Render the input box and its contents to the given surface.
        
        Args:
            surface: Pygame surface to draw on
        """
        self._draw_background(surface)
        self._draw_border(surface)
        self._draw_text(surface)
        self._draw_cursor(surface)

    def _draw_background(self, surface: pygame.Surface) -> None:
        """Draw the background rectangle of the input box."""
        pygame.draw.rect(surface, INPUT_BG_COLOR, self.rect)

    def _draw_border(self, surface: pygame.Surface) -> None:
        """Draw the border of the input box, with color based on active state."""
        border_color = (
            INPUT_ACTIVE_BORDER_COLOR if self.active else INPUT_BORDER_COLOR
        )
        pygame.draw.rect(surface, border_color, self.rect, BORDER_WIDTH)

    def _draw_text(self, surface: pygame.Surface) -> None:
        """
        Draw the text content or placeholder.
        
        Shows placeholder text when input is empty and inactive.
        Uses different colors for active/inactive and text/placeholder states.
        """
        # Determine what text to display
        display_text = self._get_display_text()
        text_color = self._get_text_color()

        # Render and position text
        text_surface = self.font.render(display_text, True, text_color)
        text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        surface.blit(text_surface, (self.rect.x + TEXT_PADDING_X, text_y))

    def _get_display_text(self) -> str:
        """
        Determine which text to display: actual text or placeholder.
        
        Returns:
            The text to render
        """
        if self.text or self.active:
            return self.text
        return self.placeholder

    def _get_text_color(self) -> tuple[int, int, int]:
        """
        Determine the text color based on input state.
        
        Returns:
            RGB color tuple
        """
        if self.text or self.active:
            return TEXT_COLOR
        return PLACEHOLDER_COLOR

    def _draw_cursor(self, surface: pygame.Surface) -> None:
        """
        Draw a blinking cursor when the input box is active.
        
        The cursor is a vertical line positioned after the current text.
        """
        if not self.active:
            return

        # Calculate cursor position based on rendered text width
        display_text = self._get_display_text()
        text_surface = self.font.render(display_text, True, TEXT_COLOR)
        cursor_x = self.rect.x + TEXT_PADDING_X + text_surface.get_width()

        # Draw vertical line cursor
        cursor_y_start = self.rect.y + TEXT_PADDING_Y
        cursor_y_end = cursor_y_start + (self.rect.height - 2 * TEXT_PADDING_Y)
        text_color = self._get_text_color()

        pygame.draw.line(
            surface,
            text_color,
            (cursor_x, cursor_y_start),
            (cursor_x, cursor_y_end),
            CURSOR_WIDTH,
        )