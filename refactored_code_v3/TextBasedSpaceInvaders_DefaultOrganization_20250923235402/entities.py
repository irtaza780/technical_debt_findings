import logging
import pygame
import settings

logger = logging.getLogger(__name__)

# Drawing constants
SHIP_BODY_WIDTH_RATIO = 0.6
SHIP_BODY_HEIGHT_RATIO = 0.5
SHIP_BODY_Y_RATIO = 0.4
SHIP_NOSE_TOP_Y = 0.0
SHIP_NOSE_LEFT_X = 0.15
SHIP_NOSE_RIGHT_X = 0.85
SHIP_NOSE_Y = 0.5
SHIP_ACCENT_X_RATIO = 0.45
SHIP_ACCENT_Y_RATIO = 0.2
SHIP_ACCENT_WIDTH_RATIO = 0.1
SHIP_ACCENT_HEIGHT_RATIO = 0.6
SHIP_ACCENT_ALPHA = 70
ACCENT_COLOR = (255, 255, 255, 70)

ALIEN_BODY_X_RATIO = 0.1
ALIEN_BODY_Y_RATIO = 0.25
ALIEN_BODY_WIDTH_RATIO = 0.8
ALIEN_BODY_HEIGHT_RATIO = 0.5
ALIEN_EYE_WIDTH_RATIO = 0.15
ALIEN_EYE_HEIGHT_RATIO = 0.2
ALIEN_LEFT_EYE_X_RATIO = 0.22
ALIEN_RIGHT_EYE_X_RATIO = 0.63
ALIEN_EYE_Y_RATIO = 0.32
ALIEN_LEG_WIDTH_RATIO = 0.18
ALIEN_LEG_HEIGHT_RATIO = 0.2
ALIEN_LEG_Y_RATIO = 0.75
ALIEN_LEG_COUNT = 4
ALIEN_LEG_START_X_RATIO = 0.12
ALIEN_LEG_SPACING_RATIO = 0.22

RECT_BORDER_RADIUS_SMALL = 2
RECT_BORDER_RADIUS_MEDIUM = 3
RECT_BORDER_RADIUS_LARGE = 6

TRANSPARENT_BLACK = (0, 0, 0, 0)
BOUNDARY_OFFSET = 0


class Player(pygame.sprite.Sprite):
    """
    Controllable player ship sprite.
    
    Handles movement left/right with keyboard input and shooting projectiles
    with cooldown management.
    """

    def __init__(self, x: int, y: int):
        """
        Initialize the player ship at the given position.
        
        Args:
            x: Center x-coordinate of the ship.
            y: Center y-coordinate of the ship.
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
        surf.fill(TRANSPARENT_BLACK)
        w, h = surf.get_size()
        hull_color = settings.GREEN
        
        # Draw body rectangle
        body_rect = pygame.Rect(
            w * SHIP_BODY_WIDTH_RATIO * 0.2,
            h * SHIP_BODY_Y_RATIO,
            w * SHIP_BODY_WIDTH_RATIO,
            h * SHIP_BODY_HEIGHT_RATIO
        )
        pygame.draw.rect(surf, hull_color, body_rect, border_radius=RECT_BORDER_RADIUS_LARGE)
        
        # Draw nose triangle pointing upward
        nose_points = [
            (w * 0.5, SHIP_NOSE_TOP_Y),
            (w * SHIP_NOSE_LEFT_X, h * SHIP_NOSE_Y),
            (w * SHIP_NOSE_RIGHT_X, h * SHIP_NOSE_Y)
        ]
        pygame.draw.polygon(surf, hull_color, nose_points)
        
        # Draw accent stripe
        accent_rect = pygame.Rect(
            w * SHIP_ACCENT_X_RATIO,
            h * SHIP_ACCENT_Y_RATIO,
            w * SHIP_ACCENT_WIDTH_RATIO,
            h * SHIP_ACCENT_HEIGHT_RATIO
        )
        pygame.draw.rect(surf, ACCENT_COLOR, accent_rect)

    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        """
        Update player position based on keyboard input.
        
        Handles left/right movement and enforces screen boundary constraints.
        
        Args:
            keys: Current keyboard state from pygame.
        """
        dx = 0
        # Check for left movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed
        # Check for right movement
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed
        
        self.rect.x += dx
        self._clamp_to_screen_bounds()

    def _clamp_to_screen_bounds(self) -> None:
        """Constrain player position within screen boundaries."""
        if self.rect.left < BOUNDARY_OFFSET:
            self.rect.left = BOUNDARY_OFFSET
        if self.rect.right > settings.WIDTH:
            self.rect.right = settings.WIDTH

    def shoot(self, now_ms: int) -> pygame.sprite.Sprite | None:
        """
        Create a bullet if the shoot cooldown has elapsed.
        
        Args:
            now_ms: Current time in milliseconds.
            
        Returns:
            A Bullet sprite if cooldown elapsed, None otherwise.
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
    
    Moves vertically and is removed when it leaves the screen.
    """

    def __init__(self, x: int, y: int, dy: int):
        """
        Initialize a bullet at the given position.
        
        Args:
            x: Center x-coordinate of the bullet.
            y: Center y-coordinate of the bullet.
            dy: Vertical velocity (pixels per frame).
        """
        super().__init__()
        self.image = pygame.Surface((settings.BULLET_WIDTH, settings.BULLET_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(
            self.image,
            settings.CYAN,
            self.image.get_rect(),
            border_radius=RECT_BORDER_RADIUS_SMALL
        )
        self.rect = self.image.get_rect(center=(x, y))
        self.dy = dy

    def update(self) -> None:
        """
        Update bullet position and remove if off-screen.
        
        Moves the bullet vertically and kills it if it exits the screen bounds.
        """
        self.rect.y += self.dy
        # Remove bullet if it travels beyond screen boundaries
        if self.rect.bottom < 0 or self.rect.top > settings.HEIGHT:
            self.kill()


class Alien(pygame.sprite.Sprite):
    """
    Enemy sprite representing an alien in the fleet.
    
    Displays a colored alien with body, eyes, and legs.
    Movement is managed by the AlienFleet controller.
    """

    def __init__(self, x: int, y: int, color_index: int = 0):
        """
        Initialize an alien sprite at the given position.
        
        Args:
            x: Top-left x-coordinate of the alien.
            y: Top-left y-coordinate of the alien.
            color_index: Index into ALIEN_COLORS for the alien's color.
        """
        super().__init__()
        w, h = settings.ALIEN_WIDTH, settings.ALIEN_HEIGHT
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        color = settings.ALIEN_COLORS[color_index % len(settings.ALIEN_COLORS)]
        self._draw_alien(color)
        self.rect = self.image.get_rect(topleft=(x, y))

    def _draw_alien(self, color: tuple) -> None:
        """
        Draw the alien sprite with body, eyes, and legs.
        
        Args:
            color: RGB or RGBA tuple for the alien's hull color.
        """
        surf = self.image
        surf.fill(TRANSPARENT_BLACK)
        w, h = surf.get_size()
        
        # Draw body
        body_rect = pygame.Rect(
            w * ALIEN_BODY_X_RATIO,
            h * ALIEN_BODY_Y_RATIO,
            w * ALIEN_BODY_WIDTH_RATIO,
            h * ALIEN_BODY_HEIGHT_RATIO
        )
        pygame.draw.rect(surf, color, body_rect, border_radius=RECT_BORDER_RADIUS_MEDIUM)
        
        # Draw eyes
        self._draw_eyes(surf, w, h, color)
        
        # Draw legs
        self._draw_legs(surf, w, h, color)

    def _draw_eyes(self, surf: pygame.Surface, width: int, height: int, color: tuple) -> None:
        """
        Draw alien eyes on the given surface.
        
        Args:
            surf: Surface to draw on.
            width: Width of the surface.
            height: Height of the surface.
            color: Color for the alien (unused, eyes are always black).
        """
        eye_w = int(width * ALIEN_EYE_WIDTH_RATIO)
        eye_h = int(height * ALIEN_EYE_HEIGHT_RATIO)
        
        left_eye = pygame.Rect(
            int(width * ALIEN_LEFT_EYE_X_RATIO),
            int(height * ALIEN_EYE_Y_RATIO),
            eye_w,
            eye_h
        )
        right_eye = pygame.Rect(
            int(width * ALIEN_RIGHT_EYE_X_RATIO),
            int(height * ALIEN_EYE_Y_RATIO),
            eye_w,
            eye_h
        )
        
        pygame.draw.rect(surf, settings.BLACK, left_eye, border_radius=RECT_BORDER_RADIUS_MEDIUM)
        pygame.draw.rect(surf, settings.BLACK, right_eye, border_radius=RECT_BORDER_RADIUS_MEDIUM)

    def _draw_legs(self, surf: pygame.Surface, width: int, height: int, color: tuple) -> None:
        """
        Draw alien legs on the given surface.
        
        Args:
            surf: Surface to draw on.
            width: Width of the surface.
            height: Height of the surface.
            color: Color for the legs.
        """
        leg_w = int(width * ALIEN_LEG_WIDTH_RATIO)
        leg_h = int(height * ALIEN_LEG_HEIGHT_RATIO)
        
        for i in range(ALIEN_LEG_COUNT):
            leg_x = int(width * (ALIEN_LEG_START_X_RATIO + i * ALIEN_LEG_SPACING_RATIO))
            leg_y = int(height * ALIEN_LEG_Y_RATIO)
            leg_rect = pygame.Rect(leg_x, leg_y, leg_w, leg_h)
            pygame.draw.rect(surf, color, leg_rect, border_radius=RECT_BORDER_RADIUS_MEDIUM)

    def update(self) -> None:
        """
        Update alien state.
        
        Movement is managed by the AlienFleet controller, not here.
        """
        pass