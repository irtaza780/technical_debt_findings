import logging
import pygame
import settings

logger = logging.getLogger(__name__)

# Drawing constants
SHIP_BODY_WIDTH_RATIO = 0.6
SHIP_BODY_HEIGHT_RATIO = 0.5
SHIP_BODY_Y_RATIO = 0.4
SHIP_BODY_X_RATIO = 0.2
SHIP_NOSE_TOP_Y = 0
SHIP_NOSE_LEFT_X_RATIO = 0.15
SHIP_NOSE_RIGHT_X_RATIO = 0.85
SHIP_NOSE_Y_RATIO = 0.5
SHIP_ACCENT_X_RATIO = 0.45
SHIP_ACCENT_Y_RATIO = 0.2
SHIP_ACCENT_WIDTH_RATIO = 0.1
SHIP_ACCENT_HEIGHT_RATIO = 0.6
SHIP_ACCENT_ALPHA = 70
SHIP_BODY_BORDER_RADIUS = 6

ALIEN_BODY_X_RATIO = 0.1
ALIEN_BODY_Y_RATIO = 0.25
ALIEN_BODY_WIDTH_RATIO = 0.8
ALIEN_BODY_HEIGHT_RATIO = 0.5
ALIEN_BODY_BORDER_RADIUS = 4
ALIEN_EYE_WIDTH_RATIO = 0.15
ALIEN_EYE_HEIGHT_RATIO = 0.2
ALIEN_LEFT_EYE_X_RATIO = 0.22
ALIEN_RIGHT_EYE_X_RATIO = 0.63
ALIEN_EYE_Y_RATIO = 0.32
ALIEN_EYE_BORDER_RADIUS = 3
ALIEN_LEG_WIDTH_RATIO = 0.18
ALIEN_LEG_HEIGHT_RATIO = 0.2
ALIEN_LEG_Y_RATIO = 0.75
ALIEN_LEG_START_X_RATIO = 0.12
ALIEN_LEG_SPACING_RATIO = 0.22
ALIEN_LEG_BORDER_RADIUS = 3
ALIEN_LEG_COUNT = 4

BULLET_BORDER_RADIUS = 2

ACCENT_WHITE_COLOR = (255, 255, 255, 70)
TRANSPARENT_COLOR = (0, 0, 0, 0)


class Player(pygame.sprite.Sprite):
    """
    Controllable player ship sprite.
    
    Handles movement left/right, screen boundary constraints, and shooting
    with cooldown management.
    """

    def __init__(self, x: int, y: int):
        """
        Initialize the player ship.
        
        Args:
            x: Initial x-coordinate (center).
            y: Initial y-coordinate (center).
        """
        super().__init__()
        self.width = settings.PLAYER_WIDTH
        self.height = settings.PLAYER_HEIGHT
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._draw_ship()
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = settings.PLAYER_SPEED
        self.last_shot_ms = 0

    def _draw_ship(self) -> None:
        """Draw a triangular ship with body, nose, and accent stripe."""
        surf = self.image
        surf.fill(TRANSPARENT_COLOR)
        w, h = surf.get_size()
        hull_color = settings.GREEN

        # Draw body rectangle
        body_rect = pygame.Rect(
            w * SHIP_BODY_X_RATIO,
            h * SHIP_BODY_Y_RATIO,
            w * SHIP_BODY_WIDTH_RATIO,
            h * SHIP_BODY_HEIGHT_RATIO
        )
        pygame.draw.rect(surf, hull_color, body_rect, border_radius=SHIP_BODY_BORDER_RADIUS)

        # Draw nose triangle
        nose_points = [
            (w * 0.5, SHIP_NOSE_TOP_Y),
            (w * SHIP_NOSE_LEFT_X_RATIO, h * SHIP_NOSE_Y_RATIO),
            (w * SHIP_NOSE_RIGHT_X_RATIO, h * SHIP_NOSE_Y_RATIO)
        ]
        pygame.draw.polygon(surf, hull_color, nose_points)

        # Draw accent stripe
        accent_rect = pygame.Rect(
            w * SHIP_ACCENT_X_RATIO,
            h * SHIP_ACCENT_Y_RATIO,
            w * SHIP_ACCENT_WIDTH_RATIO,
            h * SHIP_ACCENT_HEIGHT_RATIO
        )
        pygame.draw.rect(surf, ACCENT_WHITE_COLOR, accent_rect)

    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        """
        Update player position based on keyboard input.
        
        Handles left/right movement and enforces screen boundary constraints.
        
        Args:
            keys: Current keyboard state from pygame.
        """
        dx = self._calculate_horizontal_movement(keys)
        self.rect.x += dx
        self._constrain_to_screen_bounds()

    def _calculate_horizontal_movement(self, keys: pygame.key.ScancodeWrapper) -> int:
        """
        Calculate horizontal movement delta based on key presses.
        
        Args:
            keys: Current keyboard state.
            
        Returns:
            Horizontal movement delta in pixels.
        """
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed
        return dx

    def _constrain_to_screen_bounds(self) -> None:
        """Ensure player sprite stays within screen boundaries."""
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > settings.WIDTH:
            self.rect.right = settings.WIDTH

    def shoot(self, now_ms: int) -> pygame.sprite.Sprite | None:
        """
        Create a bullet if cooldown has elapsed.
        
        Args:
            now_ms: Current time in milliseconds.
            
        Returns:
            Bullet sprite if cooldown elapsed, None otherwise.
        """
        if now_ms - self.last_shot_ms >= settings.SHOOT_COOLDOWN_MS:
            self.last_shot_ms = now_ms
            bullet_x = self.rect.centerx
            bullet_y = self.rect.top - settings.BULLET_HEIGHT // 2
            return Bullet(bullet_x, bullet_y, dy=settings.BULLET_SPEED)
        return None


class Bullet(pygame.sprite.Sprite):
    """
    Projectile sprite fired by the player.
    
    Moves vertically and is removed when off-screen.
    """

    def __init__(self, x: int, y: int, dy: int):
        """
        Initialize a bullet sprite.
        
        Args:
            x: Initial x-coordinate (center).
            y: Initial y-coordinate (center).
            dy: Vertical velocity (pixels per frame).
        """
        super().__init__()
        self.image = pygame.Surface((settings.BULLET_WIDTH, settings.BULLET_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(self.image, settings.CYAN, self.image.get_rect(), border_radius=BULLET_BORDER_RADIUS)
        self.rect = self.image.get_rect(center=(x, y))
        self.dy = dy

    def update(self) -> None:
        """Update bullet position and remove if off-screen."""
        self.rect.y += self.dy
        if self.rect.bottom < 0 or self.rect.top > settings.HEIGHT:
            self.kill()


class Alien(pygame.sprite.Sprite):
    """
    Enemy sprite that forms part of the alien fleet.
    
    Displays a simple alien creature with body, eyes, and legs.
    Movement is managed externally by the fleet controller.
    """

    def __init__(self, x: int, y: int, color_index: int = 0):
        """
        Initialize an alien sprite.
        
        Args:
            x: Initial x-coordinate (top-left).
            y: Initial y-coordinate (top-left).
            color_index: Index into ALIEN_COLORS list (wraps if out of range).
        """
        super().__init__()
        w, h = settings.ALIEN_WIDTH, settings.ALIEN_HEIGHT
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        color = settings.ALIEN_COLORS[color_index % len(settings.ALIEN_COLORS)]
        self._draw_alien(color)
        self.rect = self.image.get_rect(topleft=(x, y))

    def _draw_alien(self, color: tuple) -> None:
        """
        Draw alien sprite with body, eyes, and legs.
        
        Args:
            color: RGB color tuple for the alien body.
        """
        surf = self.image
        surf.fill(TRANSPARENT_COLOR)
        w, h = surf.get_size()

        self._draw_alien_body(surf, w, h, color)
        self._draw_alien_eyes(surf, w, h)
        self._draw_alien_legs(surf, w, h, color)

    def _draw_alien_body(self, surf: pygame.Surface, w: int, h: int, color: tuple) -> None:
        """
        Draw the main body rectangle of the alien.
        
        Args:
            surf: Surface to draw on.
            w: Surface width.
            h: Surface height.
            color: RGB color tuple.
        """
        body_rect = pygame.Rect(
            w * ALIEN_BODY_X_RATIO,
            h * ALIEN_BODY_Y_RATIO,
            w * ALIEN_BODY_WIDTH_RATIO,
            h * ALIEN_BODY_HEIGHT_RATIO
        )
        pygame.draw.rect(surf, color, body_rect, border_radius=ALIEN_BODY_BORDER_RADIUS)

    def _draw_alien_eyes(self, surf: pygame.Surface, w: int, h: int) -> None:
        """
        Draw the alien's two eyes.
        
        Args:
            surf: Surface to draw on.
            w: Surface width.
            h: Surface height.
        """
        eye_w = int(w * ALIEN_EYE_WIDTH_RATIO)
        eye_h = int(h * ALIEN_EYE_HEIGHT_RATIO)

        left_eye = pygame.Rect(
            int(w * ALIEN_LEFT_EYE_X_RATIO),
            int(h * ALIEN_EYE_Y_RATIO),
            eye_w,
            eye_h
        )
        right_eye = pygame.Rect(
            int(w * ALIEN_RIGHT_EYE_X_RATIO),
            int(h * ALIEN_EYE_Y_RATIO),
            eye_w,
            eye_h
        )

        pygame.draw.rect(surf, settings.BLACK, left_eye, border_radius=ALIEN_EYE_BORDER_RADIUS)
        pygame.draw.rect(surf, settings.BLACK, right_eye, border_radius=ALIEN_EYE_BORDER_RADIUS)

    def _draw_alien_legs(self, surf: pygame.Surface, w: int, h: int, color: tuple) -> None:
        """
        Draw the alien's four legs.
        
        Args:
            surf: Surface to draw on.
            w: Surface width.
            h: Surface height.
            color: RGB color tuple.
        """
        leg_w = int(w * ALIEN_LEG_WIDTH_RATIO)
        leg_h = int(h * ALIEN_LEG_HEIGHT_RATIO)

        for i in range(ALIEN_LEG_COUNT):
            leg_x = int(w * (ALIEN_LEG_START_X_RATIO + i * ALIEN_LEG_SPACING_RATIO))
            leg_y = int(h * ALIEN_LEG_Y_RATIO)
            leg_rect = pygame.Rect(leg_x, leg_y, leg_w, leg_h)
            pygame.draw.rect(surf, color, leg_rect, border_radius=ALIEN_LEG_BORDER_RADIUS)

    def update(self) -> None:
        """
        Update alien state.
        
        Movement is managed externally by the fleet controller.
        """
        pass