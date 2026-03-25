import logging
import pygame
from settings import (
    CELL_SIZE,
    GRID_WIDTH,
    GRID_HEIGHT,
    BG_COLOR,
    GRID_COLOR,
    SNAKE_HEAD_COLOR,
    SNAKE_BODY_COLOR,
    TEXT_COLOR,
    TEXT_SHADOW,
    FOOD_SCORE,
    DIFFICULTY_SPEEDS,
    TITLE,
)
from snake import Snake
from food import Food

logger = logging.getLogger(__name__)

# Game constants
DEFAULT_MOVES_PER_SECOND = 12
MIN_MOVE_INTERVAL_MS = 40
OVERLAY_ALPHA = 120
GAME_OVER_OVERLAY_ALPHA = 140
OVERLAY_SHADOW_OFFSET = 2
PAUSE_OVERLAY_COLOR = (0, 0, 0, OVERLAY_ALPHA)
GAME_OVER_OVERLAY_COLOR = (0, 0, 0, GAME_OVER_OVERLAY_ALPHA)
HINT_TEXT_COLOR = (230, 230, 230)
HUD_POSITION = (10, 8)
PAUSE_TITLE_Y_OFFSET = -20
PAUSE_HINT_Y_OFFSET = 30
GAME_OVER_TITLE_Y_OFFSET = -40
GAME_OVER_HINT_Y_OFFSET = 20
TARGET_FPS = 60


class Game:
    """
    Encapsulates the snake game logic and rendering.
    
    Handles input processing, game state management, collision detection,
    scoring, and rendering. Implements input throttling to allow at most
    one direction change between movement ticks.
    """

    def __init__(self, screen, difficulty):
        """
        Initialize the game with a given screen and difficulty level.
        
        Args:
            screen: pygame Surface to render the game on
            difficulty: string key for difficulty level (e.g., 'easy', 'normal', 'hard')
        """
        self.screen = screen
        self.difficulty = difficulty
        self.moves_per_second = DIFFICULTY_SPEEDS.get(difficulty, DEFAULT_MOVES_PER_SECOND)
        self.clock = pygame.time.Clock()

        self._init_fonts()
        self._init_movement_timer()
        self._init_world_entities()
        self._init_game_state()
        self._init_input_mapping()

        pygame.display.set_caption(f"{TITLE} - {self.difficulty}")

    def _init_fonts(self):
        """Initialize all font objects used for rendering."""
        self.font_hud = pygame.font.SysFont("consolas", 24, bold=True)
        self.font_big = pygame.font.SysFont("arial", 48, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18)

    def _init_movement_timer(self):
        """Initialize the movement timer event."""
        self.MOVE_EVENT = pygame.USEREVENT + 1
        interval_ms = max(MIN_MOVE_INTERVAL_MS, int(1000 / self.moves_per_second))
        pygame.time.set_timer(self.MOVE_EVENT, interval_ms)

    def _init_world_entities(self):
        """Initialize snake and food entities."""
        start_pos = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
        self.snake = Snake(start_pos)
        self.food = Food(GRID_WIDTH, GRID_HEIGHT, CELL_SIZE)
        self.food.spawn(self.snake.body)

    def _init_game_state(self):
        """Initialize game state variables."""
        self.score = 0
        self.game_over = False
        self.victory = False
        self.paused = False
        self._dir_changed = False

    def _init_input_mapping(self):
        """Initialize keyboard to direction mapping."""
        self.key_dir_map = {
            pygame.K_UP: (0, -1),
            pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0),
            pygame.K_d: (1, 0),
        }

    def reset(self):
        """Reset the game state to start a new round with the same difficulty."""
        self._init_world_entities()
        self._init_game_state()

    def handle_input(self, event):
        """
        Process input events for direction changes and control keys.
        
        Throttles direction input to one accepted change per movement tick.
        
        Args:
            event: pygame event object
            
        Returns:
            "quit" to exit application, "menu" to return to menu, None otherwise
        """
        if event.type != pygame.KEYDOWN:
            return None

        # Handle pause/resume
        if event.key in (pygame.K_p, pygame.K_SPACE) and not self.game_over:
            self.paused = not self.paused
            return None

        # Handle movement (ignored while paused or game over)
        if self._should_accept_direction_input(event.key):
            self.snake.set_direction(self.key_dir_map[event.key])
            self._dir_changed = True
            return None

        # Handle restart
        if event.key == pygame.K_r:
            self.reset()
            return None

        # Handle quit
        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            return "quit"

        # Handle menu
        if event.key == pygame.K_m:
            return "menu"

        return None

    def _should_accept_direction_input(self, key):
        """
        Determine if a direction input should be accepted.
        
        Args:
            key: pygame key constant
            
        Returns:
            True if the key is a direction key and input should be accepted
        """
        return (
            key in self.key_dir_map
            and not self.game_over
            and not self.paused
            and not self._dir_changed
        )

    def step(self):
        """
        Perform one movement tick.
        
        Moves the snake, handles food consumption, detects collisions,
        updates score, and checks for victory. Resets direction-change
        throttle at the start of the tick.
        """
        if self.game_over or self.paused:
            return

        # Allow one new direction change for the interval after this movement
        self._dir_changed = False

        next_head = self._next_head_pos()

        # Check boundary collision
        if not self._is_within_bounds(next_head):
            self.game_over = True
            return

        # Determine if snake will eat food
        will_eat = self.food.position == next_head

        # Move snake (grow if eating)
        self.snake.move(grow=will_eat)

        # Check self collision
        if self.snake.collides_with_self():
            self.game_over = True
            return

        # Handle food consumption
        if will_eat:
            self._handle_food_consumption()

    def _is_within_bounds(self, position):
        """
        Check if a position is within the game grid bounds.
        
        Args:
            position: tuple of (x, y) coordinates
            
        Returns:
            True if position is within bounds
        """
        x, y = position
        return 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT

    def _handle_food_consumption(self):
        """Handle the logic when the snake eats food."""
        self.score += FOOD_SCORE
        spawned = self.food.spawn(self.snake.body)
        if not spawned:
            # No free cells left; player filled the board
            self.game_over = True
            self.victory = True

    def _next_head_pos(self):
        """
        Compute the next head position based on current direction.
        
        Returns:
            tuple of (x, y) for the next head position
        """
        hx, hy = self.snake.head
        dx, dy = self.snake.direction
        return (hx + dx, hy + dy)

    def draw_grid(self, surface):
        """
        Draw a background grid to make movement clearer.
        
        Args:
            surface: pygame Surface to draw on
        """
        # Draw vertical lines
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(
                surface,
                GRID_COLOR,
                (x * CELL_SIZE, 0),
                (x * CELL_SIZE, GRID_HEIGHT * CELL_SIZE),
                1,
            )
        # Draw horizontal lines
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(
                surface,
                GRID_COLOR,
                (0, y * CELL_SIZE),
                (GRID_WIDTH * CELL_SIZE, y * CELL_SIZE),
                1,
            )

    def _draw_snake(self, surface):
        """
        Draw the snake on the surface.
        
        Args:
            surface: pygame Surface to draw on
        """
        for i, (x, y) in enumerate(self.snake.body):
            is_body = i < len(self.snake.body) - 1
            color = SNAKE_BODY_COLOR if is_body else SNAKE_HEAD_COLOR
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, color, rect)

    def _draw_hud(self, surface):
        """
        Draw the heads-up display with score and difficulty.
        
        Args:
            surface: pygame Surface to draw on
        """
        paused_tag = "  [PAUSED]" if self.paused and not self.game_over else ""
        score_text = f"Score: {self.score}    {self.difficulty}{paused_tag}"
        score_surf = self.font_hud.render(score_text, True, TEXT_COLOR)
        surface.blit(score_surf, HUD_POSITION)

    def _draw_pause_overlay(self, surface):
        """
        Draw the pause overlay with instructions.
        
        Args:
            surface: pygame Surface to draw on
        """
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill(PAUSE_OVERLAY_COLOR)
        surface.blit(overlay, (0, 0))

        self._draw_centered_text(
            surface,
            "Paused",
            self.font_big,
            PAUSE_TITLE_Y_OFFSET,
        )

        hint_text = "Press P/Space to resume    R to restart    M for menu    ESC/Q to quit"
        self._draw_centered_text(
            surface,
            hint_text,
            self.font_small,
            PAUSE_HINT_Y_OFFSET,
            HINT_TEXT_COLOR,
        )

    def _draw_game_over_overlay(self, surface):
        """
        Draw the game over overlay with final score and instructions.
        
        Args:
            surface: pygame Surface to draw on
        """
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill(GAME_OVER_OVERLAY_COLOR)
        surface.blit(overlay, (0, 0))

        title = "You Win!" if self.victory else "Game Over"
        self._draw_centered_text(
            surface,
            title,
            self.font_big,
            GAME_OVER_TITLE_Y_OFFSET,
        )

        hint_text = "Press R to restart    M for menu    ESC/Q to quit"
        self._draw_centered_text(
            surface,
            hint_text,
            self.font_small,
            GAME_OVER_HINT_Y_OFFSET,
            HINT_TEXT_COLOR,
        )

    def _draw_centered_text(self, surface, text, font, y_offset, color=TEXT_COLOR):
        """
        Draw text centered horizontally with a shadow effect.
        
        Args:
            surface: pygame Surface to draw on
            text: string to render
            font: pygame font object
            y_offset: vertical offset from center
            color: text color (default TEXT_COLOR)
        """
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(
            center=(surface.get_width() // 2, surface.get_height() // 2 + y_offset)
        )

        # Draw shadow
        shadow_surf = font.render(text, True, TEXT_SHADOW)
        shadow_rect = shadow_surf.get_rect(
            center=(text_rect.centerx + OVERLAY_SHADOW_OFFSET, text_rect.centery + OVERLAY_SHADOW_OFFSET)
        )
        surface.blit(shadow_surf, shadow_rect)
        surface.blit(text_surf, text_rect)

    def draw(self, surface):
        """
        Render the complete game state.
        
        Includes snake, food, score, and any overlays (pause/game over).
        
        Args:
            surface: pygame Surface to draw on
        """
        surface.fill(BG_COLOR)
        self.draw_grid(surface)

        # Draw game entities
        self.food.draw(surface)
        self._draw_snake(surface)

        # Draw HUD
        self._draw_hud(surface)

        # Draw overlays
        if self.paused and not self.game_over:
            self._draw_pause_overlay(surface)

        if self.game_over:
            self._draw_game_over_overlay(surface)

    def run(self):
        """
        Main game loop for a single session.
        
        Returns:
            "menu" to return to menu, "quit" to exit application
            
        Ensures the MOVE_EVENT timer is stopped when leaving the loop
        to avoid ghost events during menus or other scenes.
        """
        try:
            while True:
                self.clock.tick(TARGET_FPS)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return "quit"

                    result = self.handle_input(event)
                    if result in ("quit", "menu"):
                        return result

                    # Process movement tick
                    if event.type == self.MOVE_EVENT and not self.game_over and not self.paused:
                        self.step()

                self.draw(self.screen)
                pygame.display.flip()
        except Exception as e:
            logger.exception("Error in game loop: %s", e)
            raise
        finally:
            # Ensure the movement timer is stopped when leaving the game loop
            pygame.time.set_timer(self.MOVE_EVENT, 0)
            # Flush any pending MOVE_EVENTs from the queue before returning
            pygame.event.clear(self.MOVE_EVENT)