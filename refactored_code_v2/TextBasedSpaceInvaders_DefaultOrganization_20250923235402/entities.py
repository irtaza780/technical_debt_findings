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
ALIEN_LEG_COUNT = 4
ALIEN_LEG_BORDER_RADIUS = 3

BULLET_BORDER_RADIUS = 2

TRANSPARENT_BLACK = (0, 0, 0, 0)
ACCENT_COLOR = (255, 255, 255, 70)

SCREEN_BOUNDARY_OFFSET = 0


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
            x: Center x-coordinate of the ship
            y: Center y-coordinate of the ship
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
        self.image.fill(TRANSPARENT_BLACK)
        width, height = self.image.get_size()
        
        # Draw ship body
        self._draw_ship_body(width, height)
        
        # Draw ship nose
        self._draw_ship_nose(width, height)
        
        # Draw accent stripe
        self._draw_ship_accent(width, height)

    def _draw_ship_body(self, width: int, height: int) -> None:
        """
        Draw the main body rectangle of the ship.
        
        Args:
            width: Surface width
            height: Surface height
        """
        body_rect = pygame.Rect(
            width * SHIP_BODY_WIDTH_RATIO * 0.2,
            height * SHIP_BODY_Y_RATIO,
            width * SHIP_BODY_WIDTH_RATIO,
            height * SHIP_BODY_HEIGHT_RATIO
        )
        pygame.draw.rect(
            self.image,
            settings.GREEN,
            body_rect,
            border_radius=SHIP_BODY_BORDER_RADIUS
        )

    def _draw_ship_nose(self, width: int, height: int) -> None:
        """
        Draw the triangular nose of the ship.
        
        Args:
            width: Surface width
            height: Surface height
        """
        nose_points = [
            (width * 0.5, height * SHIP_NOSE_TOP_Y),
            (width * SHIP_NOSE_LEFT_X, height * SHIP_NOSE_Y),
            (width * SHIP_NOSE_RIGHT_X, height * SHIP_NOSE_Y)
        ]
        pygame.draw.polygon(self.image, settings.GREEN, nose_points)

    def _draw_ship_accent(self, width: int, height: int) -> None:
        """
        Draw the accent stripe on the ship.
        
        Args:
            width: Surface width
            height: Surface height
        """
        accent_rect = pygame.Rect(
            width * SHIP_ACCENT_X_RATIO,
            height * SHIP_ACCENT_Y_RATIO,
            width * SHIP_ACCENT_WIDTH_RATIO,
            height * SHIP_ACCENT_HEIGHT_RATIO
        )
        pygame.draw.rect(self.image, ACCENT_COLOR, accent_rect)

    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        """
        Update player position based on keyboard input.
        
        Moves left/right and clamps position within screen bounds.
        
        Args:
            keys: Pygame key state wrapper
        """
        dx = self._calculate_movement(keys)
        self.rect.x += dx
        self._clamp_to_screen_bounds()

    def _calculate_movement(self, keys: pygame.key.ScancodeWrapper) -> int:
        """
        Calculate horizontal movement delta based on key input.
        
        Args:
            keys: Pygame key state wrapper
            
        Returns:
            Horizontal movement delta in pixels
        """
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed
        return dx

    def _clamp_to_screen_bounds(self) -> None:
        """Ensure the player sprite stays within screen boundaries."""
        if self.rect.left < SCREEN_BOUNDARY_OFFSET:
            self.rect.left = SCREEN_BOUNDARY_OFFSET
        if self.rect.right > settings.WIDTH:
            self.rect.right = settings.WIDTH

    def shoot(self, now_ms: int) -> pygame.sprite.Sprite | None:
        """
        Create a bullet if the shoot cooldown has elapsed.
        
        Args:
            now_ms: Current time in milliseconds
            
        Returns:
            A Bullet sprite if cooldown elapsed, None otherwise
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
            x: Center x-coordinate
            y: Center y-coordinate
            dy: Vertical velocity (pixels per frame)
        """
        super().__init__()
        self.image = pygame.Surface(
            (settings.BULLET_WIDTH, settings.BULLET_HEIGHT),
            pygame.SRCALPHA
        )
        pygame.draw.rect(
            self.image,
            settings.CYAN,
            self.image.get_rect(),
            border_radius=BULLET_BORDER_RADIUS
        )
        self.rect = self.image.get_rect(center=(x, y))
        self.dy = dy

    def update(self) -> None:
        """
        Update bullet position and remove if off-screen.
        
        Moves vertically and kills the sprite when it exits the screen bounds.
        """
        self.rect.y += self.dy
        if self.rect.bottom < 0 or self.rect.top > settings.HEIGHT:
            self.kill()


class Alien(pygame.sprite.Sprite):
    """
    Enemy sprite that forms part of the alien fleet.
    
    Displays a simple alien creature with body, eyes, and legs.
    Movement is managed externally by the AlienFleet class.
    """

    def __init__(self, x: int, y: int, color_index: int = 0):
        """
        Initialize an alien sprite at the given position.
        
        Args:
            x: Top-left x-coordinate
            y: Top-left y-coordinate
            color_index: Index into ALIEN_COLORS list (wraps if out of range)
        """
        super().__init__()
        width, height = settings.ALIEN_WIDTH, settings.ALIEN_HEIGHT
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        color = settings.ALIEN_COLORS[color_index % len(settings.ALIEN_COLORS)]
        self._draw_alien(color)
        self.rect = self.image.get_rect(topleft=(x, y))

    def _draw_alien(self, color: tuple) -> None:
        """
        Draw the alien sprite with body, eyes, and legs.
        
        Args:
            color: RGB color tuple for the alien
        """
        self.image.fill(TRANSPARENT_BLACK)
        width, height = self.image.get_size()
        
        # Draw body
        self._draw_alien_body(width, height, color)
        
        # Draw eyes
        self._draw_alien_eyes(width, height)
        
        # Draw legs
        self._draw_alien_legs(width, height, color)

    def _draw_alien_body(self, width: int, height: int, color: tuple) -> None:
        """
        Draw the main body of the alien.
        
        Args:
            width: Surface width
            height: Surface height
            color: RGB color tuple
        """
        body_rect = pygame.Rect(
            width * ALIEN_BODY_X_RATIO,
            height * ALIEN_BODY_Y_RATIO,
            width * ALIEN_BODY_WIDTH_RATIO,
            height * ALIEN_BODY_HEIGHT_RATIO
        )
        pygame.draw.rect(
            self.image,
            color,
            body_rect,
            border_radius=ALIEN_BODY_BORDER_RADIUS
        )

    def _draw_alien_eyes(self, width: int, height: int) -> None:
        """
        Draw the two eyes of the alien.
        
        Args:
            width: Surface width
            height: Surface height
        """
        eye_width = int(width * ALIEN_EYE_WIDTH_RATIO)
        eye_height = int(height * ALIEN_EYE_HEIGHT_RATIO)
        eye_y = int(height * ALIEN_EYE_Y_RATIO)
        
        left_eye = pygame.Rect(
            int(width * ALIEN_LEFT_EYE_X_RATIO),
            eye_y,
            eye_width,
            eye_height
        )
        right_eye = pygame.Rect(
            int(width * ALIEN_RIGHT_EYE_X_RATIO),
            eye_y,
            eye_width,
            eye_height
        )
        
        pygame.draw.rect(
            self.image,
            settings.BLACK,
            left_eye,
            border_radius=ALIEN_EYE_BORDER_RADIUS
        )
        pygame.draw.rect(
            self.image,
            settings.BLACK,
            right_eye,
            border_radius=ALIEN_EYE_BORDER_RADIUS
        )

    def _draw_alien_legs(self, width: int, height: int, color: tuple) -> None:
        """
        Draw the four legs of the alien.
        
        Args:
            width: Surface width
            height: Surface height
            color: RGB color tuple
        """
        leg_width = int(width * ALIEN_LEG_WIDTH_RATIO)
        leg_height = int(height * ALIEN_LEG_HEIGHT_RATIO)
        leg_y = int(height * ALIEN_LEG_Y_RATIO)
        
        for i in range(ALIEN_LEG_COUNT):
            leg_x = int(width * (ALIEN_LEG_START_X_RATIO + i * ALIEN_LEG_SPACING_RATIO))
            leg_rect = pygame.Rect(leg_x, leg_y, leg_width, leg_height)
            pygame.draw.rect(
                self.image,
                color,
                leg_rect,
                border_radius=ALIEN_LEG_BORDER_RADIUS
            )

    def update(self) -> None:
        """
        Update alien state.
        
        Movement is managed externally by the AlienFleet class.
        """