from __future__ import annotations

import logging
from typing import TYPE_CHECKING

try:
    import pygame
except ImportError as e:
    pygame = None

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GROUND_HEIGHT,
    PIPE_WIDTH,
    BIRD_SIZE,
    BIRD_COLOR,
    BIRD_OUTLINE,
    PIPE_COLOR,
    PIPE_OUTLINE,
    GRAVITY,
    FLAP_STRENGTH,
    MAX_DROP_SPEED,
)

if TYPE_CHECKING:
    import pygame

logger = logging.getLogger(__name__)

PYGAME_REQUIRED_ERROR = (
    "pygame is required to construct sprites. Please install it with: pip install pygame"
)

BIRD_BEAK_WIDTH = 8
BIRD_BEAK_HEIGHT = 6
BIRD_BEAK_X_OFFSET = 6
BIRD_EYE_X_OFFSET = 3
BIRD_EYE_Y_OFFSET = 5
BIRD_EYE_OUTER_RADIUS = 5
BIRD_EYE_INNER_RADIUS = 2
BIRD_EYE_WHITE = (255, 255, 255)
BIRD_EYE_BLACK = (0, 0, 0)
BIRD_BEAK_COLOR = (250, 190, 20)

ROTATION_VELOCITY_SCALE = 4.0
ROTATION_MAX_VELOCITY = 20.0
ROTATION_MIN_VELOCITY = -15.0
ROTATION_SCALE_FACTOR = 3.0
ROTATION_MAX_DEGREES = 45.0
ROTATION_MIN_DEGREES = -45.0

PIPE_OUTLINE_WIDTH = 2


def _check_pygame_available() -> None:
    """
    Verify that pygame is available, raising RuntimeError if not.

    Raises:
        RuntimeError: If pygame module is not installed.
    """
    if pygame is None:
        raise RuntimeError(PYGAME_REQUIRED_ERROR)


class Bird:
    """
    The player's bird character with simple physics and drawing.

    Attributes:
        x: Horizontal position of the bird.
        y: Vertical position of the bird.
        vy: Vertical velocity of the bird.
        rotation_deg: Current rotation angle in degrees.
        base_image: The base sprite image before rotation.
    """

    def __init__(self, x: int, y: int) -> None:
        """
        Initialize the bird at position (x, y).

        Args:
            x: Initial horizontal position.
            y: Initial vertical position.

        Raises:
            RuntimeError: If pygame is not installed.
        """
        _check_pygame_available()
        self.x: float = float(x)
        self.y: float = float(y)
        self.vy: float = 0.0
        self.rotation_deg: float = 0.0
        self.base_image = self._create_bird_sprite()

    def _create_bird_sprite(self) -> pygame.Surface:
        """
        Create the bird sprite image with circle body, beak, and eye.

        Returns:
            A pygame Surface containing the bird sprite.
        """
        surface = pygame.Surface((BIRD_SIZE, BIRD_SIZE), pygame.SRCALPHA)
        center = BIRD_SIZE // 2
        radius = center - 2

        self._draw_bird_body(surface, center, radius)
        self._draw_bird_beak(surface, center)
        self._draw_bird_eye(surface, center)

        return surface

    def _draw_bird_body(
        self, surface: pygame.Surface, center: int, radius: int
    ) -> None:
        """
        Draw the circular body of the bird.

        Args:
            surface: The surface to draw on.
            center: The center coordinate of the bird.
            radius: The radius of the bird circle.
        """
        pygame.draw.circle(surface, BIRD_COLOR, (center, center), radius)
        pygame.draw.circle(surface, BIRD_OUTLINE, (center, center), radius, width=2)

    def _draw_bird_beak(self, surface: pygame.Surface, center: int) -> None:
        """
        Draw the beak of the bird.

        Args:
            surface: The surface to draw on.
            center: The vertical center coordinate of the bird.
        """
        beak_points = [
            (BIRD_SIZE - BIRD_BEAK_X_OFFSET, center),
            (
                BIRD_SIZE - BIRD_BEAK_X_OFFSET - BIRD_BEAK_WIDTH,
                center - BIRD_BEAK_HEIGHT // 2,
            ),
            (
                BIRD_SIZE - BIRD_BEAK_X_OFFSET - BIRD_BEAK_WIDTH,
                center + BIRD_BEAK_HEIGHT // 2,
            ),
        ]
        pygame.draw.polygon(surface, BIRD_BEAK_COLOR, beak_points)

    def _draw_bird_eye(self, surface: pygame.Surface, center: int) -> None:
        """
        Draw the eye of the bird.

        Args:
            surface: The surface to draw on.
            center: The center coordinate of the bird.
        """
        eye_x = center - BIRD_EYE_X_OFFSET
        eye_y = center - BIRD_EYE_Y_OFFSET

        pygame.draw.circle(surface, BIRD_EYE_WHITE, (eye_x, eye_y), BIRD_EYE_OUTER_RADIUS)
        pygame.draw.circle(surface, BIRD_EYE_BLACK, (eye_x + 2, eye_y), BIRD_EYE_INNER_RADIUS)

    def flap(self) -> None:
        """
        Apply an upward impulse to the bird.
        """
        self.vy = FLAP_STRENGTH

    def update(self) -> None:
        """
        Apply gravity, update position, and calculate rotation based on velocity.
        """
        self._apply_physics()
        self._update_rotation()
        self._clamp_to_screen()

    def _apply_physics(self) -> None:
        """
        Apply gravity and update vertical position.
        """
        self.vy = min(self.vy + GRAVITY, MAX_DROP_SPEED)
        self.y += self.vy

    def _update_rotation(self) -> None:
        """
        Calculate rotation angle based on vertical velocity.

        Rotation increases (tilts down) when falling and decreases (tilts up) when rising.
        """
        # Scale velocity to rotation: higher downward velocity = more downward tilt
        velocity_clamped = max(
            min(self.vy * ROTATION_VELOCITY_SCALE, ROTATION_MAX_VELOCITY),
            ROTATION_MIN_VELOCITY,
        )
        target_rotation = -velocity_clamped * ROTATION_SCALE_FACTOR

        # Clamp final rotation to valid range
        self.rotation_deg = max(
            min(target_rotation, ROTATION_MAX_DEGREES), ROTATION_MIN_DEGREES
        )

    def _clamp_to_screen(self) -> None:
        """
        Prevent the bird from moving above the top of the screen.
        """
        top_limit = self.get_rect().height // 2
        if self.y < top_limit:
            self.y = float(top_limit)
            self.vy = 0.0

    def get_rect(self) -> pygame.Rect:
        """
        Get the current collision rectangle, centered at the bird's position.

        Returns:
            A pygame Rect representing the bird's collision bounds.
        """
        rect = pygame.Rect(0, 0, self.base_image.get_width(), self.base_image.get_height())
        rect.center = (int(self.x), int(self.y))
        return rect

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the rotated bird image on the given surface.

        Args:
            surface: The surface to draw the bird on.
        """
        rotated = pygame.transform.rotate(self.base_image, self.rotation_deg)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect.topleft)


class PipePair:
    """
    Represents a pair of pipes (top and bottom) with a vertical gap.

    The pipes move horizontally across the screen and serve as obstacles.

    Attributes:
        x: Horizontal position of the pipes.
        gap_y_top: Y coordinate of the top of the gap.
        gap_height: Height of the gap between pipes.
        speed: Horizontal movement speed (pixels per frame).
        width: Width of each pipe.
        top_rect: Collision rectangle for the top pipe.
        bottom_rect: Collision rectangle for the bottom pipe.
    """

    def __init__(self, x: int, gap_y_top: int, gap_height: int, speed: float) -> None:
        """
        Create a new PipePair.

        Args:
            x: Starting horizontal position (typically right of screen).
            gap_y_top: Y coordinate of the top of the gap.
            gap_height: Height of the gap between top and bottom pipes.
            speed: Horizontal speed in pixels per frame (moves left).

        Raises:
            RuntimeError: If pygame is not installed.
        """
        _check_pygame_available()
        self.x: float = float(x)
        self.gap_y_top: int = gap_y_top
        self.gap_height: int = gap_height
        self.speed: float = float(speed)
        self.width: int = PIPE_WIDTH
        self._passed: bool = False

        self.top_rect = pygame.Rect(0, 0, 0, 0)
        self.bottom_rect = pygame.Rect(0, 0, 0, 0)
        self._rebuild_rects()

    def _rebuild_rects(self) -> None:
        """
        Recalculate the top and bottom pipe rectangles from current position and gap.
        """
        # Top pipe extends from top of screen to gap start
        self.top_rect.update(int(self.x), 0, self.width, self.gap_y_top)

        # Bottom pipe extends from gap end to ground
        bottom_top_y = self.gap_y_top + self.gap_height
        bottom_height = max(0, SCREEN_HEIGHT - GROUND_HEIGHT - bottom_top_y)
        self.bottom_rect.update(int(self.x), bottom_top_y, self.width, bottom_height)

    def update(self) -> None:
        """
        Move pipes left according to speed and update collision rectangles.
        """
        self.x -= self.speed
        self._rebuild_rects()

    def is_offscreen(self) -> bool:
        """
        Check if the pipe has entirely moved off the left side of the screen.

        Returns:
            True if the pipe's right edge is beyond the left screen boundary.
        """
        return int(self.x) + self.width < 0

    def collides(self, bird_rect: pygame.Rect) -> bool:
        """
        Check whether the bird collides with either the top or bottom pipe.

        Args:
            bird_rect: The collision rectangle of the bird.

        Returns:
            True if the bird intersects with either pipe rectangle.
        """
        return bird_rect.colliderect(self.top_rect) or bird_rect.colliderect(self.bottom_rect)

    def check_and_flag_passed(self, bird_x: float) -> bool:
        """
        Determine if the bird has passed the pipe and mark it as passed.

        This should be called once per frame to detect when the bird successfully
        navigates through the gap. Returns True only on the first frame the bird passes.

        Args:
            bird_x: The horizontal position of the bird.

        Returns:
            True if the bird just passed the pipe (first time), False otherwise.
        """
        if not self._passed and bird_x > self.x + self.width:
            self._passed = True
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the top and bottom pipes with outlines to the given surface.

        Args:
            surface: The surface to draw the pipes on.
        """
        # Draw filled pipe rectangles
        pygame.draw.rect(surface, PIPE_COLOR, self.top_rect)
        pygame.draw.rect(surface, PIPE_COLOR, self.bottom_rect)

        # Draw outlines for visual contrast
        pygame.draw.rect(surface, PIPE_OUTLINE, self.top_rect, width=PIPE_OUTLINE_WIDTH)
        pygame.draw.rect(surface, PIPE_OUTLINE, self.bottom_rect, width=PIPE_OUTLINE_WIDTH)