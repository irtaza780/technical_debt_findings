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
SHADOW_OFFSET = 2
PAUSE_TITLE_Y_OFFSET = -20
PAUSE_HINT_Y_OFFSET = 30
GAME_OVER_TITLE_Y_OFFSET = -40
GAME_OVER_HINT_Y_OFFSET = 20
HINT_TEXT_COLOR = (230, 230, 230)
GRID_LINE_WIDTH = 1
FPS_LIMIT = 60
FONT_HUD_SIZE = 24
FONT_BIG_SIZE = 48
FONT_SMALL_SIZE = 18


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
        """Initialize all font objects used for rendering text."""
        self.font_hud = pygame.font.SysFont("consolas", FONT_HUD_SIZE, bold=True)
        self.font_big = pygame.font.SysFont("arial", FONT_BIG_SIZE, bold=True)
        self.font_small = pygame.font.SysFont("arial", FONT_SMALL_SIZE)

    def _init_movement_timer(self):
        """Initialize the movement timer event for game ticks."""
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
        logger.info(f"Game reset at difficulty: {self.difficulty}")

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
            logger.debug(f"Game paused: {self.paused}")
            return None

        # Handle movement input with throttling
        if self._is_movement_key(event.key):
            if not self.game_over and not self.paused and not self._dir_changed:
                self.snake.set_direction(self.key_dir_map[event.key])
                self._dir_changed = True
            return None

        # Handle control keys
        if event.key == pygame.K_r:
            self.reset()
            return None

        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            return "quit"

        if event.key == pygame.K_m:
            return "menu"

        return None

    def _is_movement_key(self, key):
        """
        Check if a key is a movement key.
        
        Args:
            key: pygame key constant
            
        Returns:
            True if key is mapped to a direction, False otherwise
        """
        return key in self.key_dir_map

    def step(self):
        """
        Perform one movement tick: move snake, handle food consumption,
        detect collisions, update score, and check victory condition.
        
        Resets direction-change throttle at the start of the tick.
        """
        if self.game_over or self.paused:
            return

        # Allow one new direction change for the next interval
        self._dir_changed = False

        next_head = self._next_head_pos()

        # Check boundary collision
        if not self._is_within_bounds(next_head):
            self.game_over = True
            logger.info("Game over: boundary collision")
            return

        # Check if snake will eat food
        will_eat = self.food.position == next_head

        # Move snake (grow if eating)
        self.snake.move(grow=will_eat)

        # Check self collision
        if self.snake.collides_with_self():
            self.game_over = True
            logger.info("Game over: self collision")
            return

        # Handle food consumption
        if will_eat:
            self.score += FOOD_SCORE
            spawned = self.food.spawn(self.snake.body)
            if not spawned:
                # No free cells left; player filled the board
                self.game_over = True
                self.victory = True
                logger.info(f"Victory! Final score: {self.score}")

    def _next_head_pos(self):
        """
        Compute the next head position based on current direction.
        
        Returns:
            Tuple of (x, y) coordinates for the next head position
        """
        hx, hy = self.snake.head
        dx, dy = self.snake.direction
        return (hx + dx, hy + dy)

    def _is_within_bounds(self, position):
        """
        Check if a position is within the game grid bounds.
        
        Args:
            position: Tuple of (x, y) coordinates
            
        Returns:
            True if position is within bounds, False otherwise
        """
        x, y = position
        return 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT

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
                GRID_LINE_WIDTH,
            )

        # Draw horizontal lines
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(
                surface,
                GRID_COLOR,
                (0, y * CELL_SIZE),
                (GRID_WIDTH * CELL_SIZE, y * CELL_SIZE),
                GRID_LINE_WIDTH,
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
        Draw the heads-up display (score and difficulty).
        
        Args:
            surface: pygame Surface to draw on
        """
        paused_tag = "  [PAUSED]" if self.paused and not self.game_over else ""
        score_text = f"Score: {self.score}    {self.difficulty}{paused_tag}"
        score_surf = self.font_hud.render(score_text, True, TEXT_COLOR)
        surface.blit(score_surf, (10, 8))

    def _draw_pause_overlay(self, surface):
        """
        Draw the pause overlay with instructions.
        
        Args:
            surface: pygame Surface to draw on
        """
        # Semi-transparent overlay
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, OVERLAY_ALPHA))
        surface.blit(overlay, (0, 0))

        # Title with shadow
        title = "Paused"
        self._draw_text_with_shadow(
            surface,
            title,
            self.font_big,
            (surface.get_width() // 2, surface.get_height() // 2 + PAUSE_TITLE_Y_OFFSET),
        )

        # Instructions
        hint_text = "Press P/Space to resume    R to restart    M for menu    ESC/Q to quit"
        hint_surf = self.font_small.render(hint_text, True, HINT_TEXT_COLOR)
        hint_pos = hint_surf.get_rect(
            center=(surface.get_width() // 2, surface.get_height() // 2 + PAUSE_HINT_Y_OFFSET)
        )
        surface.blit(hint_surf, hint_pos)

    def _draw_game_over_overlay(self, surface):
        """
        Draw the game over overlay with final score and instructions.
        
        Args:
            surface: pygame Surface to draw on
        """
        # Semi-transparent overlay
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, GAME_OVER_OVERLAY_ALPHA))
        surface.blit(overlay, (0, 0))

        # Title with shadow
        title = "You Win!" if self.victory else "Game Over"
        self._draw_text_with_shadow(
            surface,
            title,
            self.font_big,
            (surface.get_width() // 2, surface.get_height() // 2 + GAME_OVER_TITLE_Y_OFFSET),
        )

        # Instructions
        hint_text = "Press R to restart    M for menu    ESC/Q to quit"
        hint_surf = self.font_small.render(hint_text, True, HINT_TEXT_COLOR)
        hint_pos = hint_surf.get_rect(
            center=(surface.get_width() // 2, surface.get_height() // 2 + GAME_OVER_HINT_Y_OFFSET)
        )
        surface.blit(hint_surf, hint_pos)

    def _draw_text_with_shadow(self, surface, text, font, center_pos):
        """
        Draw text with a shadow effect.
        
        Args:
            surface: pygame Surface to draw on
            text: string to render
            font: pygame font object
            center_pos: tuple of (x, y) for center position
        """
        shadow_surf = font.render(text, True, TEXT_SHADOW)
        text_surf = font.render(text, True, TEXT_COLOR)

        text_rect = text_surf.get_rect(center=center_pos)
        shadow_rect = shadow_surf.get_rect(
            center=(center_pos[0] + SHADOW_OFFSET, center_pos[1] + SHADOW_OFFSET)
        )

        surface.blit(shadow_surf, shadow_rect)
        surface.blit(text_surf, text_rect)

    def draw(self, surface):
        """
        Render the complete game state including snake, food, score, and overlays.
        
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
            
        Ensures the MOVE_EVENT timer is stopped when leaving the loop to avoid
        ghost events during menus or other scenes.
        """
        try:
            while True:
                self.clock.tick(FPS_LIMIT)

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
            logger.error(f"Error in game loop: {e}", exc_info=True)
            raise
        finally:
            # Ensure the movement timer is stopped when leaving the game loop
            pygame.time.set_timer(self.MOVE_EVENT, 0)
            # Flush any pending MOVE_EVENTs from the queue before returning
            pygame.event.clear(self.MOVE_EVENT)