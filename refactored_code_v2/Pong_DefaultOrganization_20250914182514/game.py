import logging
import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE,
    COLOR_BG, COLOR_FG, COLOR_DIM, COLOR_ACCENT,
    PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED,
    BALL_RADIUS, BALL_START_SPEED, BALL_MAX_SPEED, BALL_SPEEDUP_FACTOR,
    WINNING_SCORE, SERVE_COOLDOWN_MS, FPS,
    SCORE_FONT_SIZE, INFO_FONT_SIZE, WIN_FONT_SIZE,
    CENTER_DASH_HEIGHT, CENTER_DASH_GAP
)
from entities import Paddle, Ball

# Constants
PADDLE_MARGIN = 24
INITIAL_SERVE_DELAY_MS = 800
SCORE_DISPLAY_Y = 20
SCORE_LEFT_X_RATIO = 0.25
SCORE_RIGHT_X_RATIO = 0.75
WIN_MESSAGE_Y_OFFSET = -40
WIN_INFO_Y_OFFSET = 10
COOLDOWN_DISPLAY_Y_RATIO = 0.5
CONTROLS_HINT_Y_OFFSET = -32
CONTROLS_HINT_COLOR = (100, 100, 110)
COOLDOWN_ROUNDING_FACTOR = 0.9
CENTER_LINE_WIDTH = 4
CENTER_LINE_X_OFFSET = -2

logger = logging.getLogger(__name__)


class Game:
    """Main game controller for Two-Player Pong."""

    def __init__(self):
        """Initialize pygame, window, entities, fonts, and game state."""
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self._initialize_fonts()
        self._initialize_paddles()
        self._initialize_ball()
        self._initialize_game_state()

    def _initialize_fonts(self) -> None:
        """Initialize all game fonts."""
        self.score_font = pygame.font.SysFont(None, SCORE_FONT_SIZE)
        self.info_font = pygame.font.SysFont(None, INFO_FONT_SIZE)
        self.win_font = pygame.font.SysFont(None, WIN_FONT_SIZE)

    def _initialize_paddles(self) -> None:
        """Initialize both paddles at their starting positions."""
        left_x = PADDLE_MARGIN
        right_x = SCREEN_WIDTH - PADDLE_MARGIN - PADDLE_WIDTH
        center_y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2

        self.left_paddle = Paddle(
            left_x, center_y, PADDLE_WIDTH, PADDLE_HEIGHT,
            PADDLE_SPEED, SCREEN_HEIGHT
        )
        self.right_paddle = Paddle(
            right_x, center_y, PADDLE_WIDTH, PADDLE_HEIGHT,
            PADDLE_SPEED, SCREEN_HEIGHT
        )

    def _initialize_ball(self) -> None:
        """Initialize the ball at the center of the screen."""
        center_x = SCREEN_WIDTH / 2
        center_y = SCREEN_HEIGHT / 2
        self.ball = Ball(
            center_x, center_y, BALL_RADIUS, BALL_START_SPEED,
            SCREEN_WIDTH, SCREEN_HEIGHT,
            max_speed=BALL_MAX_SPEED,
            speedup_factor=BALL_SPEEDUP_FACTOR
        )

    def _initialize_game_state(self) -> None:
        """Initialize game state variables."""
        self.left_score = 0
        self.right_score = 0
        self.game_over = False
        self.ball_active = True
        self.serve_resume_time = 0
        self.left_dir = 0
        self.right_dir = 0

    def process_input(self) -> bool:
        """
        Process events and continuous keypress states.

        Returns:
            False to exit the game loop, True to continue running.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if self.game_over and event.key == pygame.K_r:
                    self.reset_match()

        self._update_paddle_directions()
        return True

    def _update_paddle_directions(self) -> None:
        """Update movement directions for both paddles based on key presses."""
        keys = pygame.key.get_pressed()

        # Left paddle: W/S
        up_left = keys[pygame.K_w]
        down_left = keys[pygame.K_s]

        # Right paddle: Up/Down
        up_right = keys[pygame.K_UP]
        down_right = keys[pygame.K_DOWN]

        # Calculate direction: -1 (up), 0 (neutral), 1 (down)
        self.left_dir = (-1 if up_left else 0) + (1 if down_left else 0)
        self.right_dir = (-1 if up_right else 0) + (1 if down_right else 0)

        # Clamp to valid range
        self.left_dir = max(-1, min(1, self.left_dir))
        self.right_dir = max(-1, min(1, self.right_dir))

    def reset_round(self, scored_by: str) -> None:
        """
        Handle actions after a point is scored.

        Args:
            scored_by: "left" or "right" indicating who scored.
        """
        if scored_by == "left":
            self.left_score += 1
        elif scored_by == "right":
            self.right_score += 1
        else:
            logger.warning(f"Invalid scorer: {scored_by}")
            return

        # Check win condition
        if self.left_score >= WINNING_SCORE or self.right_score >= WINNING_SCORE:
            self.game_over = True
            self.ball_active = False
            logger.info(f"Game over. Left: {self.left_score}, Right: {self.right_score}")
            return

        # Reset ball and start serve cooldown
        direction = -1 if scored_by == "right" else 1
        self.ball.reset(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, direction=direction)
        self.ball_active = False
        self.serve_resume_time = pygame.time.get_ticks() + SERVE_COOLDOWN_MS

    def reset_match(self) -> None:
        """Reset scores, ball, paddles, and state for a new match."""
        self.left_score = 0
        self.right_score = 0
        self.game_over = False

        center_y = SCREEN_HEIGHT // 2
        self.left_paddle.rect.centery = center_y
        self.right_paddle.rect.centery = center_y
        self.ball.reset(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, direction=None)

        self.ball_active = False
        self.serve_resume_time = pygame.time.get_ticks() + INITIAL_SERVE_DELAY_MS
        logger.info("Match reset")

    def update(self, dt: float) -> None:
        """
        Update the game world for a single frame.

        Args:
            dt: Delta time in seconds.
        """
        # Move paddles
        self.left_paddle.move(self.left_dir)
        self.right_paddle.move(self.right_dir)
        self.left_paddle.update(dt)
        self.right_paddle.update(dt)

        if self.game_over:
            return

        # Handle serve cooldown
        if not self.ball_active:
            if pygame.time.get_ticks() >= self.serve_resume_time:
                self.ball_active = True
            else:
                return

        # Update ball
        self.ball.update(dt, self.left_paddle, self.right_paddle)

        # Check scoring conditions
        self._check_scoring()

    def _check_scoring(self) -> None:
        """Check if ball has exited the play area and award points."""
        if self.ball.x + self.ball.radius < 0:
            self.reset_round("right")
        elif self.ball.x - self.ball.radius > SCREEN_WIDTH:
            self.reset_round("left")

    def render_center_line(self) -> None:
        """Draw a dashed vertical center line."""
        dash_height = CENTER_DASH_HEIGHT
        gap = CENTER_DASH_GAP
        x = SCREEN_WIDTH // 2 + CENTER_LINE_X_OFFSET
        y = 0

        while y < SCREEN_HEIGHT:
            rect = pygame.Rect(x, y, CENTER_LINE_WIDTH, dash_height)
            pygame.draw.rect(self.screen, COLOR_DIM, rect)
            y += dash_height + gap

    def render_scores(self) -> None:
        """Render the scores for both players at the top of the screen."""
        left_text_surface = self.score_font.render(str(self.left_score), True, COLOR_FG)
        right_text_surface = self.score_font.render(str(self.right_score), True, COLOR_FG)

        left_x = SCREEN_WIDTH * SCORE_LEFT_X_RATIO - left_text_surface.get_width() / 2
        right_x = SCREEN_WIDTH * SCORE_RIGHT_X_RATIO - right_text_surface.get_width() / 2

        self.screen.blit(left_text_surface, (left_x, SCORE_DISPLAY_Y))
        self.screen.blit(right_text_surface, (right_x, SCORE_DISPLAY_Y))

    def _render_win_screen(self) -> None:
        """Render the win screen with winner announcement and restart instructions."""
        winner = "Left Player" if self.left_score > self.right_score else "Right Player"
        win_text = f"{winner} Wins!"
        info_text = "Press R to restart • Esc to quit"

        win_surface = self.win_font.render(win_text, True, COLOR_ACCENT)
        info_surface = self.info_font.render(info_text, True, COLOR_DIM)

        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        self.screen.blit(win_surface, (center_x - win_surface.get_width() // 2, center_y + WIN_MESSAGE_Y_OFFSET))
        self.screen.blit(info_surface, (center_x - info_surface.get_width() // 2, center_y + WIN_INFO_Y_OFFSET))

    def _render_cooldown_message(self) -> None:
        """Render the serve cooldown countdown message."""
        remaining_ms = max(0, self.serve_resume_time - pygame.time.get_ticks())
        remaining_seconds = int((remaining_ms / 1000.0) + COOLDOWN_ROUNDING_FACTOR)
        cooldown_text = f"Get ready... {remaining_seconds}"

        text_surface = self.info_font.render(cooldown_text, True, COLOR_DIM)
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT * COOLDOWN_DISPLAY_Y_RATIO

        self.screen.blit(text_surface, (center_x - text_surface.get_width() // 2, center_y - text_surface.get_height() // 2))

    def _render_controls_hint(self) -> None:
        """Render the controls hint at the bottom of the screen."""
        hint_text = "Left: W/S • Right: ↑/↓ • Esc: Quit"
        hint_surface = self.info_font.render(hint_text, True, CONTROLS_HINT_COLOR)

        center_x = SCREEN_WIDTH // 2
        bottom_y = SCREEN_HEIGHT + CONTROLS_HINT_Y_OFFSET

        self.screen.blit(hint_surface, (center_x - hint_surface.get_width() // 2, bottom_y))

    def render_status(self) -> None:
        """Render status messages (cooldown or win)."""
        if self.game_over:
            self._render_win_screen()
            return

        if not self.ball_active:
            self._render_cooldown_message()

        self._render_controls_hint()

    def render(self) -> None:
        """Render the entire frame (background, center line, entities, UI)."""
        self.screen.fill(COLOR_BG)
        self.render_center_line()

        # Draw entities
        self.left_paddle.draw(self.screen, COLOR_FG)
        self.right_paddle.draw(self.screen, COLOR_FG)
        self.ball.draw(self.screen, COLOR_FG)

        # Render UI
        self.render_scores()
        self.render_status()

        pygame.display.flip()

    def run(self) -> None:
        """Main loop: process input, update simulation, and render at target FPS."""
        running = True
        self.ball_active = False
        self.serve_resume_time = pygame.time.get_ticks() + INITIAL_SERVE_DELAY_MS

        while running:
            running = self.process_input()
            dt = self.clock.tick(FPS) / 1000.0
            self.update(dt)
            self.render()

        pygame.quit()
        logger.info("Game closed")