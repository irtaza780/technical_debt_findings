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
BIRD_BEAK_COLOR = (250, 190, 20)
BIRD_EYE_WHITE = (255, 255, 255)
BIRD_EYE_BLACK = (0, 0, 0)

BIRD_ROTATION_VELOCITY_SCALE = 4.0
BIRD_ROTATION_MAX_VELOCITY = 20.0
BIRD_ROTATION_MIN_VELOCITY = -15.0
BIRD_ROTATION_SCALE = 3.0
BIRD_ROTATION_MAX_ANGLE = 45.0
BIRD_ROTATION_MIN_ANGLE = -45.0

PIPE_OUTLINE_WIDTH = 2
CIRCLE_OUTLINE_WIDTH = 2
CIRCLE_RADIUS_OFFSET = 2


def _check_pygame_available() -> None:
    """
    Verify that pygame is available, raising RuntimeError if not.

    Raises:
        RuntimeError: If pygame module is not installed.
    """
    if pygame is None:
        raise RuntimeError(PYGAME_REQUIRED_ERROR)


def _create_bird_image() -> pygame.Surface:
    """
    Create and return a bird sprite image with circle body, beak, and eye.

    Returns:
        pygame.Surface: The bird sprite image with transparency support.
    """
    bird_image = pygame.Surface((BIRD_SIZE, BIRD_SIZE), pygame.SRCALPHA)
    center = BIRD_SIZE // 2
    radius = center - CIRCLE_RADIUS_OFFSET

    pygame.draw.circle(bird_image, BIRD_COLOR, (center, center), radius)
    pygame.draw.circle(
        bird_image, BIRD_OUTLINE, (center, center), radius, width=CIRCLE_OUTLINE_WIDTH
    )

    _draw_bird_beak(bird_image, center)
    _draw_bird_eye(bird_image, center)

    return bird_image


def _draw_bird_beak(surface: pygame.Surface, center: int) -> None:
    """
    Draw the bird's beak on the given surface.

    Args:
        surface: The pygame surface to draw on.
        center: The center coordinate of the bird.
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


def _draw_bird_eye(surface: pygame.Surface, center: int) -> None:
    """
    Draw the bird's eye on the given surface.

    Args:
        surface: The pygame surface to draw on.
        center: The center coordinate of the bird.
    """
    eye_x = center - BIRD_EYE_X_OFFSET
    eye_y = center - BIRD_EYE_Y_OFFSET

    pygame.draw.circle(surface, BIRD_EYE_WHITE, (eye_x, eye_y), BIRD_EYE_OUTER_RADIUS)
    pygame.draw.circle(surface, BIRD_EYE_BLACK, (eye_x, eye_y), BIRD_EYE_INNER_RADIUS)


class Bird:
    """
    The player's bird character with physics simulation and rendering.

    Attributes:
        x: Horizontal position of the bird.
        y: Vertical position of the bird.
        vy: Vertical velocity of the bird.
        rotation_deg: Current rotation angle in degrees.
        base_image: The base sprite image before rotation.
    """

    def __init__(self, x: int, y: int) -> None:
        """
        Initialize the bird at the specified position.

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
        self.base_image = _create_bird_image()

    def flap(self) -> None:
        """
        Apply an upward impulse to the bird's velocity.
        """
        self.vy = FLAP_STRENGTH

    def update(self) -> None:
        """
        Update bird physics, position, and rotation based on gravity and velocity.
        """
        self._apply_gravity()
        self._update_position()
        self._update_rotation()
        self._clamp_to_screen_top()

    def _apply_gravity(self) -> None:
        """
        Apply gravity to vertical velocity, clamping to maximum drop speed.
        """
        self.vy = min(self.vy + GRAVITY, MAX_DROP_SPEED)

    def _update_position(self) -> None:
        """
        Update the bird's vertical position based on current velocity.
        """
        self.y += self.vy

    def _update_rotation(self) -> None:
        """
        Update rotation angle based on vertical velocity for visual feedback.
        """
        # Scale velocity to rotation angle, with clamping for smooth visual feedback
        velocity_scaled = self.vy * BIRD_ROTATION_VELOCITY_SCALE
        velocity_clamped = max(
            min(velocity_scaled, BIRD_ROTATION_MAX_VELOCITY), BIRD_ROTATION_MIN_VELOCITY
        )
        target_rotation = -velocity_clamped * BIRD_ROTATION_SCALE

        # Clamp final rotation angle
        self.rotation_deg = max(
            min(target_rotation, BIRD_ROTATION_MAX_ANGLE), BIRD_ROTATION_MIN_ANGLE
        )

    def _clamp_to_screen_top(self) -> None:
        """
        Prevent the bird from moving above the top of the screen.
        """
        top_limit = self.get_rect().height // 2
        if self.y < top_limit:
            self.y = float(top_limit)
            self.vy = 0.0

    def get_rect(self) -> pygame.Rect:
        """
        Get the current collision rectangle centered at the bird's position.

        Returns:
            pygame.Rect: The collision rectangle for the bird.
        """
        rect = pygame.Rect(
            0, 0, self.base_image.get_width(), self.base_image.get_height()
        )
        rect.center = (int(self.x), int(self.y))
        return rect

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the rotated bird sprite on the given surface.

        Args:
            surface: The pygame surface to draw on.
        """
        rotated_image = pygame.transform.rotate(self.base_image, self.rotation_deg)
        rect = rotated_image.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated_image, rect.topleft)


class PipePair:
    """
    A pair of vertical pipes with a gap between them that moves horizontally.

    Attributes:
        x: Horizontal position of the pipes.
        gap_y_top: Y coordinate of the top of the gap.
        gap_height: Height of the gap between pipes.
        speed: Horizontal movement speed (pixels per frame).
        width: Width of each pipe.
        top_rect: Collision rectangle for the top pipe.
        bottom_rect: Collision rectangle for the bottom pipe.
    """

    def __init__(
        self, x: int, gap_y_top: int, gap_height: int, speed: float
    ) -> None:
        """
        Initialize a pipe pair.

        Args:
            x: Starting horizontal position (typically right of screen).
            gap_y_top: Y coordinate of the top of the gap.
            gap_height: Height of the gap between top and bottom pipes.
            speed: Horizontal speed in pixels per frame (moving left).

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
        Recalculate collision rectangles based on current position and gap dimensions.
        """
        # Top pipe extends from top of screen to gap start
        self.top_rect.update(int(self.x), 0, self.width, self.gap_y_top)

        # Bottom pipe extends from gap end to ground
        bottom_top_y = self.gap_y_top + self.gap_height
        bottom_height = max(0, SCREEN_HEIGHT - GROUND_HEIGHT - bottom_top_y)
        self.bottom_rect.update(int(self.x), bottom_top_y, self.width, bottom_height)

    def update(self) -> None:
        """
        Move pipes left and update collision rectangles.
        """
        self.x -= self.speed
        self._rebuild_rects()

    def is_offscreen(self) -> bool:
        """
        Check if the pipe has completely moved off the left side of the screen.

        Returns:
            bool: True if the pipe is completely offscreen, False otherwise.
        """
        return int(self.x) + self.width < 0

    def collides(self, bird_rect: pygame.Rect) -> bool:
        """
        Check if the bird collides with either the top or bottom pipe.

        Args:
            bird_rect: The collision rectangle of the bird.

        Returns:
            bool: True if there is a collision, False otherwise.
        """
        return bird_rect.colliderect(self.top_rect) or bird_rect.colliderect(
            self.bottom_rect
        )

    def check_and_flag_passed(self, bird_x: float) -> bool:
        """
        Check if the bird has passed the pipe and mark it as passed.

        This method ensures a pipe is only counted as passed once.

        Args:
            bird_x: The horizontal position of the bird.

        Returns:
            bool: True if the bird just passed the pipe, False otherwise.
        """
        if not self._passed and bird_x > self.x + self.width:
            self._passed = True
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the top and bottom pipes with outlines on the given surface.

        Args:
            surface: The pygame surface to draw on.
        """
        pygame.draw.rect(surface, PIPE_COLOR, self.top_rect)
        pygame.draw.rect(surface, PIPE_COLOR, self.bottom_rect)
        pygame.draw.rect(surface, PIPE_OUTLINE, self.top_rect, width=PIPE_OUTLINE_WIDTH)
        pygame.draw.rect(
            surface, PIPE_OUTLINE, self.bottom_rect, width=PIPE_OUTLINE_WIDTH
        )