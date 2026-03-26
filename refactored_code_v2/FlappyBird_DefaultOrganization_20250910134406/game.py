from __future__ import annotations
import sys
import random
import logging
try:
    import pygame  # type: ignore
except ImportError as e:
    pygame = None  # type: ignore

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BG_COLOR, GROUND_HEIGHT, GROUND_COLOR,
    TEXT_COLOR, UI_COLOR,
    START_GAP, MIN_GAP,
    START_SPEED, MAX_SPEED,
    START_SPAWN_MS, MIN_SPAWN_MS,
)
from sprites import Bird, PipePair

logger = logging.getLogger(__name__)

# UI Constants
BIRD_START_X_RATIO = 0.3
BIRD_START_Y_RATIO = 0.5
BIRD_MENU_Y_RATIO = 0.5
PIPE_SPAWN_OFFSET_X = 20
PIPE_MARGIN_TOP = 50
PIPE_MARGIN_BOTTOM = 50
DIFFICULTY_GAP_SCALE = 6
DIFFICULTY_SPEED_SCALE = 0.20
DIFFICULTY_SPAWN_SCALE = 20
FONT_SIZE_LARGE = 64
FONT_SIZE_MEDIUM = 36
FONT_SIZE_SMALL = 24
MENU_SUBTITLE_OFFSET_Y = 70
MENU_HIGH_SCORE_OFFSET_Y = 110
GAMEOVER_TITLE_OFFSET_Y = -70
GAMEOVER_SCORE_OFFSET_Y = -20
CEILING_CLAMP_OFFSET = 0

# Game States
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_GAMEOVER = "gameover"


class Game:
    """
    Game encapsulates the main loop, game state, rendering, and input.
    Manages all game entities, difficulty scaling, and state transitions.
    """

    def __init__(self) -> None:
        """
        Initialize Pygame subsystems, screen, clock, fonts, and game entities.
        
        Raises:
            RuntimeError: If pygame is not installed.
        """
        if pygame is None:
            raise RuntimeError(
                "pygame is required to run this game. Please install it with: pip install pygame"
            )
        pygame.init()
        pygame.display.set_caption("Flappy Bird (Python)")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Initialize fonts
        self._init_fonts()
        
        # Game state
        self.state = STATE_MENU
        self.score = 0
        self.high_score = 0
        
        # Entities
        self.bird: Bird | None = None
        self.pipes: list[PipePair] = []
        
        # Difficulty parameters
        self.pipe_gap = START_GAP
        self.pipe_speed = START_SPEED
        self.spawn_interval_ms = START_SPAWN_MS
        
        # Timers
        self.last_spawn_time = 0
        
        # Prepare initial state
        self.reset()

    def _init_fonts(self) -> None:
        """Initialize all font objects used for rendering text."""
        self.font_large = pygame.font.SysFont(None, FONT_SIZE_LARGE)
        self.font_medium = pygame.font.SysFont(None, FONT_SIZE_MEDIUM)
        self.font_small = pygame.font.SysFont(None, FONT_SIZE_SMALL)

    def reset(self) -> None:
        """
        Reset the game to the initial configuration for a new session.
        Clears pipes, resets score, and reinitializes the bird.
        """
        bird_x = int(SCREEN_WIDTH * BIRD_START_X_RATIO)
        bird_y = int(SCREEN_HEIGHT * BIRD_START_Y_RATIO)
        self.bird = Bird(x=bird_x, y=bird_y)
        
        self.pipes.clear()
        self.score = 0
        
        # Reset difficulty to starting values
        self.pipe_gap = START_GAP
        self.pipe_speed = START_SPEED
        self.spawn_interval_ms = START_SPAWN_MS
        self.last_spawn_time = pygame.time.get_ticks()

    def start_game(self) -> None:
        """
        Start playing from the menu or after game over.
        Resets game state and transitions to playing state.
        """
        self.reset()
        self.state = STATE_PLAYING

    def update_difficulty(self) -> None:
        """
        Adjust difficulty progressively as score increases.
        
        Scales pipe gap (smaller), pipe speed (faster), and spawn interval (shorter)
        based on current score with linear scaling factors.
        """
        self.pipe_gap = max(MIN_GAP, START_GAP - self.score * DIFFICULTY_GAP_SCALE)
        self.pipe_speed = min(MAX_SPEED, START_SPEED + self.score * DIFFICULTY_SPEED_SCALE)
        self.spawn_interval_ms = max(
            MIN_SPAWN_MS, 
            START_SPAWN_MS - self.score * DIFFICULTY_SPAWN_SCALE
        )

    def spawn_pipe_pair(self) -> None:
        """
        Spawn a new pair of pipes with a random vertical gap within safe bounds.
        
        Ensures pipes don't spawn too close to screen edges and respects
        the current difficulty gap size.
        """
        max_top = SCREEN_HEIGHT - GROUND_HEIGHT - self.pipe_gap - PIPE_MARGIN_BOTTOM
        
        # Clamp gap position to safe bounds
        if max_top <= PIPE_MARGIN_TOP:
            gap_y_top = PIPE_MARGIN_TOP
        else:
            gap_y_top = random.randint(PIPE_MARGIN_TOP, max_top)
        
        pipe_x = SCREEN_WIDTH + PIPE_SPAWN_OFFSET_X
        pipe = PipePair(
            x=pipe_x,
            gap_y_top=gap_y_top,
            gap_height=self.pipe_gap,
            speed=self.pipe_speed
        )
        self.pipes.append(pipe)

    def _handle_flap_input(self) -> None:
        """Handle flap input based on current game state."""
        if self.state == STATE_MENU:
            self.start_game()
            self.bird.flap()
        elif self.state == STATE_PLAYING:
            self.bird.flap()
        elif self.state == STATE_GAMEOVER:
            self.start_game()
            self.bird.flap()

    def _handle_restart_input(self) -> None:
        """Handle restart input (only valid in game over state)."""
        if self.state == STATE_GAMEOVER:
            self.start_game()

    def handle_events(self) -> None:
        """
        Process user input and system events.
        Handles quit, flap, and restart actions.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    raise SystemExit
                elif event.key in (pygame.K_SPACE, pygame.K_UP):
                    self._handle_flap_input()
                elif event.key == pygame.K_r:
                    self._handle_restart_input()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_flap_input()

    def _update_menu_state(self) -> None:
        """Update game state when in menu (idle animation)."""
        self.bird.update()
        # Clamp bird to vertical center area for menu display
        self.bird.y = max(50, min(self.bird.y, SCREEN_HEIGHT // 2))

    def _check_collisions(self, bird_rect: pygame.Rect) -> bool:
        """
        Check for collisions with pipes and ground.
        
        Args:
            bird_rect: The bird's bounding rectangle.
            
        Returns:
            True if a collision occurred, False otherwise.
        """
        # Check pipe collisions
        for pipe in self.pipes:
            if pipe.collides(bird_rect):
                return True
        
        # Check ground collision
        ground_y = SCREEN_HEIGHT - GROUND_HEIGHT
        if bird_rect.bottom >= ground_y:
            return True
        
        return False

    def _handle_scoring(self) -> None:
        """
        Check for passed pipes and update score and difficulty accordingly.
        """
        bird_x = self.bird.x
        for pipe in self.pipes:
            if pipe.check_and_flag_passed(bird_x):
                self.score += 1
                if self.score > self.high_score:
                    self.high_score = self.score
                self.update_difficulty()

    def _clamp_bird_to_ceiling(self) -> None:
        """Prevent bird from going above screen top by clamping position and velocity."""
        bird_rect = self.bird.get_rect()
        if bird_rect.top <= CEILING_CLAMP_OFFSET:
            self.bird.y = bird_rect.height // 2
            self.bird.vy = 0.0

    def _update_playing_state(self) -> None:
        """
        Update game logic when in playing state.
        Handles bird physics, pipe spawning, collision detection, and scoring.
        """
        # Update bird physics
        self.bird.update()
        
        # Spawn pipes over time
        now = pygame.time.get_ticks()
        if now - self.last_spawn_time >= self.spawn_interval_ms:
            self.spawn_pipe_pair()
            self.last_spawn_time = now
        
        # Update pipes
        for pipe in self.pipes:
            pipe.update()
        
        # Check collisions first
        bird_rect = self.bird.get_rect()
        if self._check_collisions(bird_rect):
            self.state = STATE_GAMEOVER
            return
        
        # Handle scoring and difficulty if no collision
        self._handle_scoring()
        
        # Remove offscreen pipes
        self.pipes = [p for p in self.pipes if not p.is_offscreen()]
        
        # Clamp bird to ceiling
        self._clamp_bird_to_ceiling()

    def update(self) -> None:
        """
        Update game objects and logic depending on current state.
        
        Separates collision detection from scoring to prevent scoring
        on the same frame as a collision.
        """
        if self.state == STATE_MENU:
            self._update_menu_state()
        elif self.state == STATE_PLAYING:
            self._update_playing_state()

    def _render_playing_ui(self) -> None:
        """Render UI elements when game is in playing state."""
        score_surf = self.font_large.render(str(self.score), True, TEXT_COLOR)
        score_x = SCREEN_WIDTH // 2 - score_surf.get_width() // 2
        self.screen.blit(score_surf, (score_x, 20))

    def _render_menu_ui(self) -> None:
        """Render UI elements for the menu state."""
        title_text = "Flappy Bird"
        subtitle_text = "Press Space/Click to Start"
        
        title = self.font_large.render(title_text, True, UI_COLOR)
        subtitle = self.font_medium.render(subtitle_text, True, UI_COLOR)
        high_score_text = self.font_small.render(f"High Score: {self.high_score}", True, UI_COLOR)
        
        title_x = SCREEN_WIDTH // 2 - title.get_width() // 2
        subtitle_x = SCREEN_WIDTH // 2 - subtitle.get_width() // 2
        high_score_x = SCREEN_WIDTH // 2 - high_score_text.get_width() // 2
        
        title_y = SCREEN_HEIGHT // 3
        self.screen.blit(title, (title_x, title_y))
        self.screen.blit(subtitle, (subtitle_x, title_y + MENU_SUBTITLE_OFFSET_Y))
        self.screen.blit(high_score_text, (high_score_x, title_y + MENU_HIGH_SCORE_OFFSET_Y))

    def _render_gameover_ui(self) -> None:
        """Render UI elements for the game over state."""
        title_text = "Flappy Bird"
        subtitle_text = "Press Space/Click or R to Restart"
        
        title = self.font_large.render(title_text, True, UI_COLOR)
        subtitle = self.font_medium.render(subtitle_text, True, UI_COLOR)
        high_score_text = self.font_small.render(f"High Score: {self.high_score}", True, UI_COLOR)
        
        title_x = SCREEN_WIDTH // 2 - title.get_width() // 2
        subtitle_x = SCREEN_WIDTH // 2 - subtitle.get_width() // 2
        high_score_x = SCREEN_WIDTH // 2 - high_score_text.get_width() // 2
        
        title_y = SCREEN_HEIGHT // 3
        self.screen.blit(title, (title_x, title_y))
        self.screen.blit(subtitle, (subtitle_x, title_y + MENU_SUBTITLE_OFFSET_Y))
        self.screen.blit(high_score_text, (high_score_x, title_y + MENU_HIGH_SCORE_OFFSET_Y))
        
        # Game over specific text
        game_over_text = self.font_large.render("Game Over", True, UI_COLOR)
        score_text = self.font_medium.render(f"Score: {self.score}", True, UI_COLOR)
        
        game_over_x = SCREEN_WIDTH // 2 - game_over_text.get_width() // 2
        score_x = SCREEN_WIDTH // 2 - score_text.get_width() // 2
        
        game_over_y = title_y + GAMEOVER_TITLE_OFFSET_Y
        self.screen.blit(game_over_text, (game_over_x, game_over_y))
        self.screen.blit(score_text, (score_x, game_over_y + GAMEOVER_SCORE_OFFSET_Y))

    def _render_ground(self) -> None:
        """Render the ground rectangle at the bottom of the screen."""
        ground_rect = pygame.Rect(
            0,
            SCREEN_HEIGHT - GROUND_HEIGHT,
            SCREEN_WIDTH,
            GROUND_HEIGHT
        )
        pygame.draw.rect(self.screen, GROUND_COLOR, ground_rect, border_radius=0)

    def draw(self) -> None:
        """
        Draw the entire frame: background, pipes, ground, bird, and UI overlays.
        """
        self.screen.fill(BG_COLOR)
        
        # Draw game entities
        for pipe in self.pipes:
            pipe.draw(self.screen)
        
        self._render_ground()
        self.bird.draw(self.screen)
        
        # Draw state-specific UI
        if self.state == STATE_PLAYING:
            self._render_playing_ui()
        elif self.state == STATE_MENU:
            self._render_menu_ui()
        elif self.state == STATE_GAMEOVER:
            self._render_gameover_ui()
        
        pygame.display.flip()

    def run(self) -> None:
        """
        Main loop: handle events, update game state, and render at a fixed FPS.
        """
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)