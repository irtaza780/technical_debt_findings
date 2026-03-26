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
            color: RGB color tuple for text rendering.
        """
        rendered_text = self.font.render(text, True, color)
        surface.blit(rendered_text, pos)

    def _draw_horizontal_line(
        self,
        surface: pygame.Surface,
        y_position: int,
        x_start: int,
        x_end: int,
        color: Tuple[int, int, int] = C.COLOR_UI_HL,
    ) -> None:
        """
        Draw a horizontal line on the surface.

        Args:
            surface: Pygame surface to draw on.
            y_position: Y coordinate for the line.
            x_start: Starting X coordinate.
            x_end: Ending X coordinate.
            color: RGB color tuple for the line.
        """
        pygame.draw.line(surface, color, (x_start, y_position), (x_end, y_position))

    def _get_ui_rect(self, screen: pygame.Surface) -> pygame.Rect:
        """
        Calculate the UI sidebar rectangle dimensions.

        Args:
            screen: Pygame surface representing the game window.

        Returns:
            Pygame Rect object defining the UI sidebar area.
        """
        return pygame.Rect(
            C.GRID_WIDTH * C.TILE_SIZE, 0, C.UI_WIDTH, C.WINDOW_HEIGHT
        )

    def _draw_player_stats(
        self, surface: pygame.Surface, player: Player, level: int, x_pos: int, y_pos: int
    ) -> int:
        """
        Draw player level and HP information.

        Args:
            surface: Pygame surface to draw on.
            player: Player entity with stats.
            level: Current dungeon level.
            x_pos: X coordinate for text placement.
            y_pos: Starting Y coordinate.

        Returns:
            Updated Y coordinate after drawing.
        """
        self._draw_text(surface, LEVEL_LABEL.format(level), (x_pos, y_pos))
        y_pos += LINE_HEIGHT
        self._draw_text(surface, HP_LABEL.format(player.hp), (x_pos, y_pos))
        y_pos += LARGE_LINE_HEIGHT
        return y_pos

    def _draw_last_encounter(
        self,
        surface: pygame.Surface,
        last_monster_info: Optional[Dict[str, Any]],
        x_pos: int,
        y_pos: int,
    ) -> int:
        """
        Draw information about the last encountered monster.

        Args:
            surface: Pygame surface to draw on.
            last_monster_info: Dictionary with monster stats or None if no encounter.
            x_pos: X coordinate for text placement.
            y_pos: Starting Y coordinate.

        Returns:
            Updated Y coordinate after drawing.
        """
        self._draw_text(surface, LAST_ENCOUNTER_LABEL, (x_pos, y_pos))
        y_pos += LINE_HEIGHT

        if last_monster_info is not None:
            # Extract monster stats with fallback values
            monster_hp = last_monster_info.get("hp", "?")
            damage_taken = last_monster_info.get("damage", "?")

            self._draw_text(surface, MONSTER_HP_LABEL.format(monster_hp), (x_pos, y_pos))
            y_pos += SMALL_LINE_HEIGHT
            self._draw_text(
                surface, DAMAGE_TAKEN_LABEL.format(damage_taken), (x_pos, y_pos)
            )
            y_pos += SMALL_LINE_HEIGHT
        else:
            self._draw_text(surface, NO_ENCOUNTER_TEXT, (x_pos, y_pos))
            y_pos += SMALL_LINE_HEIGHT

        return y_pos

    def _wrap_and_draw_message(
        self, surface: pygame.Surface, message: str, x_pos: int, y_pos: int
    ) -> int:
        """
        Draw a message with word wrapping to fit within UI width.

        Args:
            surface: Pygame surface to draw on.
            message: Message text to display.
            x_pos: X coordinate for text placement.
            y_pos: Starting Y coordinate.

        Returns:
            Updated Y coordinate after drawing.
        """
        if not message:
            return y_pos

        self._draw_text(surface, MESSAGE_LABEL, (x_pos, y_pos))
        y_pos += SMALL_LINE_HEIGHT

        # Calculate maximum width for wrapped text
        max_text_width = C.UI_WIDTH - (UI_PADDING * 2)
        words = message.split()
        current_line = ""

        for word in words:
            # Attempt to add word to current line
            test_line = f"{current_line} {word}".strip()
            line_width = self.font.size(test_line)[0]

            if line_width <= max_text_width:
                current_line = test_line
            else:
                # Current line is full, draw it and start new line
                if current_line:
                    self._draw_text(surface, current_line, (x_pos, y_pos))
                    y_pos += 20
                current_line = word

        # Draw remaining text
        if current_line:
            self._draw_text(surface, current_line, (x_pos, y_pos))
            y_pos += 20

        return y_pos

    def _draw_controls(
        self, surface: pygame.Surface, x_pos: int, y_pos: int, x_end: int
    ) -> None:
        """
        Draw control instructions at the bottom of the UI.

        Args:
            surface: Pygame surface to draw on.
            x_pos: X coordinate for text placement.
            y_pos: Starting Y coordinate.
            x_end: Right edge X coordinate for separator line.
        """
        self._draw_horizontal_line(surface, y_pos, x_pos, x_end)
        y_pos += SEPARATOR_SPACING

        self._draw_text(surface, CONTROLS_LABEL, (x_pos, y_pos))
        y_pos += LINE_HEIGHT
        self._draw_text(surface, MOVE_CONTROL_TEXT, (x_pos, y_pos))
        y_pos += 20
        self._draw_text(surface, RESTART_CONTROL_TEXT, (x_pos, y_pos))
        y_pos += 20
        self._draw_text(surface, QUIT_CONTROL_TEXT, (x_pos, y_pos))

    def draw(
        self,
        screen: pygame.Surface,
        player: Player,
        level: int,
        last_monster_info: Optional[Dict[str, Any]],
        message: str,
    ) -> None:
        """
        Render the complete UI sidebar with all information.

        Args:
            screen: Pygame surface to draw on.
            player: Player entity with current stats.
            level: Current dungeon level.
            last_monster_info: Dictionary with last encountered monster stats or None.
            message: Current message to display to the player.
        """
        # Draw UI background
        ui_rect = self._get_ui_rect(screen)
        pygame.draw.rect(screen, C.COLOR_UI_BG, ui_rect)

        x_pos = ui_rect.x + UI_PADDING
        x_end = ui_rect.right - UI_PADDING
        y_pos = UI_PADDING

        # Draw title
        self._draw_text(screen, TITLE_TEXT, (x_pos, y_pos))
        y_pos += LARGE_LINE_HEIGHT
        self._draw_horizontal_line(screen, y_pos, x_pos, x_end)
        y_pos += SEPARATOR_SPACING

        # Draw player stats section
        y_pos = self._draw_player_stats(screen, player, level, x_pos, y_pos)

        # Draw last encounter section
        y_pos = self._draw_last_encounter(screen, last_monster_info, x_pos, y_pos)

        y_pos += 10
        self._draw_horizontal_line(screen, y_pos, x_pos, x_end)
        y_pos += SEPARATOR_SPACING

        # Draw message section
        y_pos = self._wrap_and_draw_message(screen, message, x_pos, y_pos)

        # Draw controls section at bottom
        controls_y_pos = C.WINDOW_HEIGHT - CONTROLS_OFFSET_FROM_BOTTOM
        self._draw_controls(screen, x_pos, controls_y_pos, x_end)