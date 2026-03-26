import logging
import pygame
import random
import settings
from entities import Player, Bullet, Alien

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
STARFIELD_SEED = 1
STARFIELD_STAR_COUNT = 80
STARFIELD_STAR_SIZE = 2
STARFIELD_COLOR = (40, 40, 40)
FLEET_DIRECTION_RIGHT = 1
FLEET_DIRECTION_LEFT = -1
LIFE_ICON_WIDTH = 22
LIFE_ICON_HEIGHT = 14
LIFE_ICON_SPACING = 28
HUD_SCORE_X = 12
HUD_SCORE_Y = 10
HUD_LIVES_X = settings.WIDTH - 180
HUD_LIVES_Y = 10
HUD_LIVES_ICONS_X = settings.WIDTH - 110
HUD_LIVES_ICONS_Y = 12
CENTERED_MESSAGE_TITLE_OFFSET_Y = -30
CENTERED_MESSAGE_SUBTITLE_OFFSET_Y = 20
GAME_STATE_START = "START"
GAME_STATE_PLAYING = "PLAYING"
GAME_STATE_GAME_OVER = "GAME_OVER"
GAME_STATE_VICTORY = "VICTORY"


class AlienFleet:
    """Manages collective alien movement, descent behavior, and fleet boundaries."""

    def __init__(self, aliens_group: pygame.sprite.Group):
        """
        Initialize the alien fleet.

        Args:
            aliens_group: pygame.sprite.Group containing all alien sprites.
        """
        self.aliens = aliens_group
        self.direction = FLEET_DIRECTION_RIGHT
        self.speed = settings.FLEET_START_SPEED
        self.drop_distance = settings.FLEET_DROP_DISTANCE

    def reset_speed(self):
        """Reset fleet direction and speed to initial values."""
        self.direction = FLEET_DIRECTION_RIGHT
        self.speed = settings.FLEET_START_SPEED

    def bounds(self) -> tuple[int, int] | None:
        """
        Calculate the leftmost and rightmost x-coordinates of the fleet.

        Returns:
            Tuple of (min_x, max_x) or None if fleet is empty.
        """
        if len(self.aliens) == 0:
            return None
        min_x = min(alien.rect.left for alien in self.aliens)
        max_x = max(alien.rect.right for alien in self.aliens)
        return min_x, max_x

    def _check_boundary_collision(self) -> bool:
        """
        Check if fleet has hit left or right screen boundary.

        Returns:
            True if boundary collision detected, False otherwise.
        """
        bounds = self.bounds()
        if bounds is None:
            return False

        min_x, max_x = bounds
        hit_right = self.direction > 0 and max_x >= settings.WIDTH - settings.FLEET_MARGIN_X
        hit_left = self.direction < 0 and min_x <= settings.FLEET_MARGIN_X
        return hit_right or hit_left

    def _drop_and_reverse(self):
        """Drop fleet down and reverse horizontal direction, then increase speed."""
        for alien in self.aliens:
            alien.rect.y += self.drop_distance
        self.direction *= -1
        self.speed *= settings.FLEET_SPEEDUP_FACTOR

    def _move_horizontally(self):
        """Move all aliens horizontally based on current direction and speed."""
        for alien in self.aliens:
            # Approximate sub-pixel movement by rounding speed each frame
            alien.rect.x += int(self.direction * round(self.speed))

    def update(self):
        """Update fleet position: handle boundary collisions and horizontal movement."""
        if len(self.aliens) == 0:
            return

        if self._check_boundary_collision():
            self._drop_and_reverse()

        self._move_horizontally()

    def reached_bottom(self, y_limit: int) -> bool:
        """
        Check if any alien has reached or passed the specified y-coordinate.

        Args:
            y_limit: Vertical cutoff in screen coordinates (typically screen height).

        Returns:
            True if any alien has reached the limit, False otherwise.
        """
        if len(self.aliens) == 0:
            return False
        max_bottom = max(alien.rect.bottom for alien in self.aliens)
        return max_bottom >= y_limit


class Game:
    """Main game controller managing game loop, state, input, updates, and rendering."""

    def __init__(self):
        """Initialize pygame, display, game state, and sprite groups."""
        self._init_pygame()
        self._init_display()
        self._init_background()
        self._init_fonts()
        self._init_game_state()
        self._init_sprite_groups()
        self.new_game()

    def _init_pygame(self):
        """Initialize pygame core components."""
        self.clock = pygame.time.Clock()

    def _init_display(self):
        """Initialize pygame display and window."""
        self.screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
        pygame.display.set_caption(settings.TITLE)

    def _init_background(self):
        """Pre-render starfield background with deterministic random seed."""
        self.bg = pygame.Surface((settings.WIDTH, settings.HEIGHT))
        self.bg.fill(settings.DARK_GRAY)
        rng = random.Random(STARFIELD_SEED)
        for _ in range(STARFIELD_STAR_COUNT):
            x = rng.randint(0, settings.WIDTH - 1)
            y = rng.randint(0, settings.HEIGHT - 1)
            self.bg.fill(STARFIELD_COLOR, rect=pygame.Rect(x, y, STARFIELD_STAR_SIZE, STARFIELD_STAR_SIZE))

    def _init_fonts(self):
        """Initialize font objects for rendering text."""
        self.font_big = pygame.font.SysFont(None, settings.BIG_FONT_SIZE)
        self.font_hud = pygame.font.SysFont(None, settings.HUD_FONT_SIZE)
        self.font_small = pygame.font.SysFont(None, settings.SMALL_FONT_SIZE)

    def _init_game_state(self):
        """Initialize game state variables."""
        self.running = True
        self.state = GAME_STATE_START
        self.score = 0
        self.lives = settings.PLAYER_LIVES
        self.player_safe_until_ms = 0

    def _init_sprite_groups(self):
        """Initialize sprite group containers."""
        self.all_sprites = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.player = None
        self.fleet = None

    def new_game(self):
        """Reset all game state and spawn initial entities for a new game."""
        self.all_sprites.empty()
        self.aliens.empty()
        self.bullets.empty()

        self._spawn_player()
        self._spawn_fleet()
        self._reset_game_stats()

    def _spawn_player(self):
        """Create and add player sprite to the game."""
        start_x = settings.WIDTH // 2
        start_y = settings.HEIGHT - settings.PLAYER_Y_OFFSET
        self.player = Player(start_x, start_y)
        self.all_sprites.add(self.player)

    def _spawn_fleet(self):
        """Create and initialize alien fleet."""
        self.spawn_aliens(settings.ALIEN_ROWS, settings.ALIEN_COLS)
        self.fleet = AlienFleet(self.aliens)
        self.fleet.reset_speed()

    def _reset_game_stats(self):
        """Reset score, lives, and game state."""
        self.score = 0
        self.lives = settings.PLAYER_LIVES
        self.player_safe_until_ms = 0
        self.state = GAME_STATE_START

    def spawn_aliens(self, rows: int, cols: int):
        """
        Spawn a grid of aliens.

        Args:
            rows: Number of rows in the alien grid.
            cols: Number of columns in the alien grid.
        """
        grid_width = cols * settings.ALIEN_WIDTH + (cols - 1) * settings.ALIEN_X_SPACING
        start_x = (settings.WIDTH - grid_width) // 2
        y = settings.FLEET_TOP_OFFSET

        for r in range(rows):
            x = start_x
            for c in range(cols):
                alien = Alien(x, y, color_index=r)
                self.aliens.add(alien)
                self.all_sprites.add(alien)
                x += settings.ALIEN_WIDTH + settings.ALIEN_X_SPACING
            y += settings.ALIEN_HEIGHT + settings.ALIEN_Y_SPACING

    def handle_events(self):
        """Process pygame events and update game state accordingly."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

        self._handle_shooting()

    def _handle_keydown(self, event: pygame.event.Event):
        """
        Handle keyboard key press events.

        Args:
            event: pygame.event.Event of type KEYDOWN.
        """
        if event.key == pygame.K_ESCAPE:
            self.running = False
            return

        if self.state in (GAME_STATE_START, GAME_STATE_GAME_OVER, GAME_STATE_VICTORY):
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.new_game()
                self.state = GAME_STATE_PLAYING

    def _handle_shooting(self):
        """Handle player shooting during gameplay."""
        if self.state != GAME_STATE_PLAYING:
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            now = pygame.time.get_ticks()
            bullet = self.player.shoot(now)
            if bullet is not None:
                self.bullets.add(bullet)
                self.all_sprites.add(bullet)

    def update(self):
        """Update game state, entities, and check win/lose conditions."""
        if self.state == GAME_STATE_PLAYING:
            keys = pygame.key.get_pressed()
            self.player.update(keys)
            self.bullets.update()
            self.fleet.update()

            self.resolve_collisions()

            if self.fleet.reached_bottom(settings.HEIGHT):
                self.state = GAME_STATE_GAME_OVER
                logger.info("Game Over: Aliens reached the bottom")

            if len(self.aliens) == 0:
                self.state = GAME_STATE_VICTORY
                logger.info(f"Victory! Final score: {self.score}")

        self.clock.tick(settings.FPS)

    def resolve_collisions(self):
        """Detect and handle all collision events."""
        self._handle_bullet_alien_collisions()
        self._handle_player_alien_collisions()

    def _handle_bullet_alien_collisions(self):
        """Handle collisions between player bullets and aliens."""
        hits = pygame.sprite.groupcollide(self.aliens, self.bullets, True, True)
        if hits:
            destroyed_aliens = len(hits)
            self.score += destroyed_aliens * settings.SCORE_PER_ALIEN

    def _handle_player_alien_collisions(self):
        """Handle collisions between player and aliens with invulnerability."""
        now = pygame.time.get_ticks()
        if now >= self.player_safe_until_ms:
            collided = pygame.sprite.spritecollide(self.player, self.aliens, dokill=False)
            if collided:
                self.lose_life()

    def lose_life(self):
        """Decrease lives, reset player position, and grant temporary invulnerability."""
        self.lives -= 1
        logger.info(f"Life lost. Remaining lives: {self.lives}")

        if self.lives <= 0:
            self.state = GAME_STATE_GAME_OVER
            logger.info("Game Over: No lives remaining")
            return

        self._reset_player_position()
        self.player_safe_until_ms = pygame.time.get_ticks() + settings.INVULNERABLE_MS
        self._clear_bullets()

    def _reset_player_position(self):
        """Reset player to center of screen."""
        self.player.rect.centerx = settings.WIDTH // 2
        self.player.rect.centery = settings.HEIGHT - settings.PLAYER_Y_OFFSET

    def _clear_bullets(self):
        """Remove all active bullets from the game."""
        for bullet in list(self.bullets):
            bullet.kill()

    def draw(self):
        """Render all game elements to the screen."""
        self.screen.blit(self.bg, (0, 0))
        self.all_sprites.draw(self.screen)
        self._draw_hud()
        self._draw_state_overlay()
        pygame.display.flip()

    def _draw_hud(self):
        """Draw heads-up display with score and lives."""
        self._draw_score()
        self._draw_lives()

    def _draw_score(self):
        """Draw score text in top-left corner."""
        score_surf = self.font_hud.render(f"Score: {self.score}", True, settings.WHITE)
        self.screen.blit(score_surf, (HUD_SCORE_X, HUD_SCORE_Y))

    def _draw_lives(self):
        """Draw lives label and life icons."""
        lives_text = self.font_hud.render("Lives:", True, settings.WHITE)
        self.screen.blit(lives_text, (HUD_LIVES_X, HUD_LIVES_Y))

        for i in range(self.lives):
            self._draw_life_icon(i)

    def _draw_life_icon(self, index: int):
        """
        Draw a single life icon (ship silhouette).

        Args:
            index: Position index for the life icon.
        """
        x = HUD_LIVES_ICONS_X + index * LIFE_ICON_SPACING
        y = HUD_LIVES_ICONS_Y
        points = [
            (x + LIFE_ICON_WIDTH // 2, y),
            (x, y + LIFE_ICON_HEIGHT),
            (x + LIFE_ICON_WIDTH, y + LIFE_ICON_HEIGHT),
        ]
        pygame.draw.polygon(self.screen, settings.GREEN, points)

    def _draw_state_overlay(self):
        """Draw state-specific overlay messages."""
        if self.state == GAME_STATE_START:
            self._draw_centered_message("Simple Space Invaders", "Press Enter or Space to Start")
        elif self.state == GAME_STATE_GAME_OVER:
            self._draw_centered_message("Game Over", "Press Enter or Space to Restart")
        elif self.state == GAME_STATE_VICTORY:
            self._draw_centered_message("You Win!", "Press Enter or Space to Play Again")

    def _draw_centered_message(self, title: str, subtitle: str):
        """
        Draw centered title and subtitle text.

        Args:
            title: Main title text.
            subtitle: Subtitle text below the title.
        """
        title_surf = self.font_big.render(title, True, settings.YELLOW)
        subtitle_surf = self.font_small.render(subtitle, True, settings.WHITE)

        title_rect = title_surf.get_rect(
            center=(settings.WIDTH // 2, settings.HEIGHT // 2 + CENTERED_MESSAGE_TITLE_OFFSET_Y)
        )
        subtitle_rect = subtitle_surf.get_rect(
            center=(settings.WIDTH // 2, settings.HEIGHT // 2 + CENTERED