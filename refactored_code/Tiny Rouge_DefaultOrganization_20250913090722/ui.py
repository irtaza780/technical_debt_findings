import logging
import pygame
from typing import Optional, Tuple, Dict, Any

import constants as C
from entities import Player

logger = logging.getLogger(__name__)

# UI Layout Constants
UI_PADDING = 12
LINE_HEIGHT = 24
SMALL_LINE_HEIGHT = 22
LARGE_LINE_HEIGHT = 28
SEPARATOR_SPACING = 12
CONTROLS_OFFSET_FROM_BOTTOM = 120

# UI Text Constants
TITLE_TEXT = "Roguelike"
LEVEL_LABEL = "Level: {}"
HP_LABEL = "HP: {}"
LAST_ENCOUNTER_LABEL = "Last Encounter:"
MONSTER_HP_LABEL = "Monster HP: {}"
DAMAGE_TAKEN_LABEL = "Damage taken: {}"
NO_ENCOUNTER_TEXT = "(none)"
MESSAGE_LABEL = "Message:"
CONTROLS_LABEL = "Controls:"
MOVE_CONTROL_TEXT = "W/A/S/D: Move"
RESTART_CONTROL_TEXT = "R: Restart"
QUIT_CONTROL_TEXT = "Esc/Q: Quit"


class UI:
    """Renders the game UI sidebar with player stats, monster info, and controls."""

    def __init__(self, font: pygame.font.Font) -> None:
        """
        Initialize the UI renderer.

        Args:
            font: Pygame font object for rendering text.
        """
        self.font = font

    def _draw_text(
        self,
        surface: pygame.Surface,
        text: str,
        pos: Tuple[int, int],
        color: Tuple[int, int, int] = C.COLOR_UI_TEXT,
    ) -> None:
        """
        Draw text on the given surface at the specified position.

        Args:
            surface: Pygame surface to draw on.
            text: Text string to render.
            pos: (x, y) position tuple for text placement.
            color: RGB color tuple (default: UI text color).
        """
        rendered_text = self.font.render(text, True, color)
        surface.blit(rendered_text, pos)

    def _draw_separator_line(
        self, surface: pygame.Surface, ui_rect: pygame.Rect, y: int
    ) -> None:
        """
        Draw a horizontal separator line in the UI.

        Args:
            surface: Pygame surface to draw on.
            ui_rect: Rectangle defining the UI area bounds.
            y: Y-coordinate for the line.
        """
        x_start = ui_rect.x + UI_PADDING
        x_end = ui_rect.right - UI_PADDING
        pygame.draw.line(surface, C.COLOR_UI_HL, (x_start, y), (x_end, y))

    def _draw_player_stats(
        self, surface: pygame.Surface, x0: int, y: int, player: Player, level: int
    ) -> int:
        """
        Draw player level and HP information.

        Args:
            surface: Pygame surface to draw on.
            x0: X-coordinate for text placement.
            y: Starting Y-coordinate.
            player: Player entity with stats.
            level: Current dungeon level.

        Returns:
            Updated Y-coordinate after drawing.
        """
        self._draw_text(surface, LEVEL_LABEL.format(level), (x0, y), C.COLOR_UI_TEXT)
        y += LINE_HEIGHT
        self._draw_text(surface, HP_LABEL.format(player.hp), (x0, y), C.COLOR_UI_TEXT)
        y += LARGE_LINE_HEIGHT
        return y

    def _draw_last_encounter(
        self,
        surface: pygame.Surface,
        x0: int,
        y: int,
        last_monster_info: Optional[Dict[str, Any]],
    ) -> int:
        """
        Draw information about the last encountered monster.

        Args:
            surface: Pygame surface to draw on.
            x0: X-coordinate for text placement.
            y: Starting Y-coordinate.
            last_monster_info: Dictionary with monster stats or None.

        Returns:
            Updated Y-coordinate after drawing.
        """
        self._draw_text(
            surface, LAST_ENCOUNTER_LABEL, (x0, y), C.COLOR_UI_TEXT
        )
        y += LINE_HEIGHT

        if last_monster_info is not None:
            # Extract monster stats with fallback values
            monster_hp = last_monster_info.get("hp", "?")
            damage_taken = last_monster_info.get("damage", "?")

            self._draw_text(
                surface,
                MONSTER_HP_LABEL.format(monster_hp),
                (x0, y),
                C.COLOR_UI_TEXT,
            )
            y += SMALL_LINE_HEIGHT
            self._draw_text(
                surface,
                DAMAGE_TAKEN_LABEL.format(damage_taken),
                (x0, y),
                C.COLOR_UI_TEXT,
            )
            y += SMALL_LINE_HEIGHT
        else:
            self._draw_text(surface, NO_ENCOUNTER_TEXT, (x0, y), C.COLOR_UI_TEXT)
            y += SMALL_LINE_HEIGHT

        return y

    def _wrap_and_draw_message(
        self, surface: pygame.Surface, x0: int, y: int, message: str
    ) -> int:
        """
        Draw a message with word wrapping to fit within UI width.

        Args:
            surface: Pygame surface to draw on.
            x0: X-coordinate for text placement.
            y: Starting Y-coordinate.
            message: Message text to display.

        Returns:
            Updated Y-coordinate after drawing.
        """
        self._draw_text(surface, MESSAGE_LABEL, (x0, y), C.COLOR_UI_TEXT)
        y += SMALL_LINE_HEIGHT

        # Calculate maximum width for wrapped text
        max_width = C.UI_WIDTH - (UI_PADDING * 2)
        words = message.split()
        current_line = ""

        for word in words:
            # Attempt to add word to current line
            test_line = f"{current_line} {word}".strip()
            line_width = self.font.size(test_line)[0]

            if line_width <= max_width:
                current_line = test_line
            else:
                # Current line is full, draw it and start new line
                if current_line:
                    self._draw_text(surface, current_line, (x0, y), C.COLOR_UI_TEXT)
                    y += SMALL_LINE_HEIGHT
                current_line = word

        # Draw remaining text
        if current_line:
            self._draw_text(surface, current_line, (x0, y), C.COLOR_UI_TEXT)
            y += SMALL_LINE_HEIGHT

        return y

    def _draw_controls(
        self, surface: pygame.Surface, x0: int, ui_rect: pygame.Rect
    ) -> None:
        """
        Draw control instructions at the bottom of the UI.

        Args:
            surface: Pygame surface to draw on.
            x0: X-coordinate for text placement.
            ui_rect: Rectangle defining the UI area bounds.
        """
        y = C.WINDOW_HEIGHT - CONTROLS_OFFSET_FROM_BOTTOM
        self._draw_separator_line(surface, ui_rect, y)
        y += SEPARATOR_SPACING

        self._draw_text(surface, CONTROLS_LABEL, (x0, y), C.COLOR_UI_TEXT)
        y += SMALL_LINE_HEIGHT
        self._draw_text(surface, MOVE_CONTROL_TEXT, (x0, y), C.COLOR_UI_TEXT)
        y += SMALL_LINE_HEIGHT
        self._draw_text(surface, RESTART_CONTROL_TEXT, (x0, y), C.COLOR_UI_TEXT)
        y += SMALL_LINE_HEIGHT
        self._draw_text(surface, QUIT_CONTROL_TEXT, (x0, y), C.COLOR_UI_TEXT)

    def draw(
        self,
        screen: pygame.Surface,
        player: Player,
        level: int,
        last_monster_info: Optional[Dict[str, Any]],
        message: str,
    ) -> None:
        """
        Draw the complete UI sidebar with all information.

        Args:
            screen: Pygame surface to draw on.
            player: Player entity with current stats.
            level: Current dungeon level.
            last_monster_info: Dictionary with last encountered monster stats or None.
            message: Current message to display to the player.
        """
        # Create UI background rectangle
        ui_rect = pygame.Rect(
            C.GRID_WIDTH * C.TILE_SIZE, 0, C.UI_WIDTH, C.WINDOW_HEIGHT
        )
        pygame.draw.rect(screen, C.COLOR_UI_BG, ui_rect)

        x0 = ui_rect.x + UI_PADDING
        y = UI_PADDING

        # Draw title
        self._draw_text(screen, TITLE_TEXT, (x0, y), C.COLOR_UI_TEXT)
        y += LARGE_LINE_HEIGHT
        self._draw_separator_line(screen, ui_rect, y)
        y += SEPARATOR_SPACING

        # Draw player stats section
        y = self._draw_player_stats(screen, x0, y, player, level)

        # Draw last encounter section
        y = self._draw_last_encounter(screen, x0, y, last_monster_info)
        y += SEPARATOR_SPACING
        self._draw_separator_line(screen, ui_rect, y)
        y += SEPARATOR_SPACING

        # Draw message section if present
        if message:
            y = self._wrap_and_draw_message(screen, x0, y, message)

        # Draw controls section
        self._draw_controls(screen, x0, ui_rect)