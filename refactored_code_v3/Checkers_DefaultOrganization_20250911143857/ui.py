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
            self._handle_mouse_click(event)
        elif event.type == pygame.KEYDOWN and self.active:
            return self._handle_key_press(event)
        
        return None

    def _handle_mouse_click(self, event: pygame.event.EventType) -> None:
        """
        Handle mouse click events to activate/deactivate the input box.
        
        Args:
            event: Pygame mouse button event
        """
        self.active = self.rect.collidepoint(event.pos)

    def _handle_key_press(self, event: pygame.event.EventType) -> Optional[str]:
        """
        Handle keyboard input when the input box is active.
        
        Args:
            event: Pygame keyboard event
            
        Returns:
            The submitted text if Enter was pressed, None otherwise
        """
        if event.key == pygame.K_RETURN:
            return self._submit_text()
        elif event.key == pygame.K_BACKSPACE:
            self._delete_last_character()
        elif event.key == pygame.K_ESCAPE:
            self._deactivate()
        elif event.unicode and event.unicode.isprintable():
            self.text += event.unicode
        
        return None

    def _submit_text(self) -> str:
        """
        Submit the current text and clear the input box.
        
        Returns:
            The submitted text
        """
        submitted = self.text
        self.text = ""
        logger.debug(f"Text submitted: {submitted}")
        return submitted

    def _delete_last_character(self) -> None:
        """Remove the last character from the input text."""
        self.text = self.text[:-1]

    def _deactivate(self) -> None:
        """Deactivate the input box without submitting."""
        self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        """
        Render the input box on the given surface.
        
        Draws the background, border, text/placeholder, and cursor (if active).
        
        Args:
            surface: Pygame surface to draw on
        """
        self._draw_background(surface)
        self._draw_border(surface)
        self._draw_text(surface)
        
        if self.active:
            self._draw_cursor(surface)

    def _draw_background(self, surface: pygame.Surface) -> None:
        """
        Draw the input box background.
        
        Args:
            surface: Pygame surface to draw on
        """
        pygame.draw.rect(surface, INPUT_BG_COLOR, self.rect)

    def _draw_border(self, surface: pygame.Surface) -> None:
        """
        Draw the input box border, with color based on active state.
        
        Args:
            surface: Pygame surface to draw on
        """
        border_color = (
            INPUT_ACTIVE_BORDER_COLOR if self.active else INPUT_BORDER_COLOR
        )
        pygame.draw.rect(surface, border_color, self.rect, BORDER_WIDTH)

    def _draw_text(self, surface: pygame.Surface) -> None:
        """
        Draw the input text or placeholder.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Determine what text to display and its color
        display_text = self._get_display_text()
        text_color = self._get_text_color()
        
        # Render and position the text
        text_surface = self.font.render(display_text, True, text_color)
        text_x = self.rect.x + TEXT_PADDING_X
        text_y = self.rect.y + (self.rect.h - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))

    def _get_display_text(self) -> str:
        """
        Determine which text to display: input text or placeholder.
        
        Returns:
            The text to display
        """
        if self.text or self.active:
            return self.text
        return self.placeholder

    def _get_text_color(self) -> tuple:
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
        Draw the text cursor when the input box is active.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Calculate cursor position based on current text width
        text_surface = self.font.render(self._get_display_text(), True, TEXT_COLOR)
        cursor_x = self.rect.x + TEXT_PADDING_X + text_surface.get_width()
        cursor_y = self.rect.y + TEXT_PADDING_Y
        cursor_height = self.rect.h - (TEXT_PADDING_Y * 2)
        
        # Draw vertical line cursor
        pygame.draw.line(
            surface,
            TEXT_COLOR,
            (cursor_x, cursor_y),
            (cursor_x, cursor_y + cursor_height),
            CURSOR_WIDTH,
        )