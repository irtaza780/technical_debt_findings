import logging
import pygame
from board import Board
from rules import GameState
from move_parser import MoveParser, MoveParseError
from ui import InputBox
from constants import (
    WIDTH, HEIGHT, BOARD_SIZE, PANEL_HEIGHT, FPS,
    BG_COLOR, TEXT_COLOR, INFO_TEXT_COLOR, STATUS_OK_COLOR, STATUS_ERR_COLOR
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# UI Constants
FONT_SIZE_SMALL = 18
FONT_SIZE_MEDIUM = 22
FONT_SIZE_LARGE = 28
PANEL_BG_COLOR = (30, 30, 30)
TURN_LABEL_Y_OFFSET = 30
STATUS_LABEL_Y_OFFSET = 54
INSTRUCTIONS_Y_OFFSET = 22
INPUT_BOX_X = 10
INPUT_BOX_Y_OFFSET = 10
INPUT_BOX_WIDTH_MARGIN = 20
INPUT_BOX_HEIGHT = 36

# Game Messages
INITIAL_STATUS_MESSAGE = "Red to move. Forced captures are enforced."
NEW_GAME_MESSAGE = "New game started. Red to move."
PARSE_ERROR_MESSAGE = "Parse error: {}"
MOVE_ACCEPTED_MESSAGE = "Move accepted. {} to move."
ILLEGAL_MOVE_MESSAGE = "Illegal move."
GAME_OVER_WIN_MESSAGE = "Game over: {} wins! ({}) - Press R to restart."
GAME_OVER_DRAW_MESSAGE = "Game over: Draw. ({}) - Press R to restart."
INSTRUCTIONS_TEXT = "Type move and press Enter. R: restart, H: help, ESC: quit."
HELP_TEXT = [
    "Help:",
    "- Enter moves using coordinates a-h for columns and 1-8 for rows.",
    "- Examples:",
    "  b6-c5           (simple move)",
    "  c3:e5:g7        (multiple captures)",
    "- Separators '-', ':', 'x', 'to' and spaces are accepted.",
    "- Forced captures are enforced.",
    "- Men move and capture forward only; kings move and capture both ways.",
    "- Press R to restart, ESC to quit."
]


class GameApp:
    """
    Main application class for Checkers (Draughts) game.
    
    Manages the game loop, rendering, user input handling, and game state.
    """

    def __init__(self):
        """Initialize the Checkers game application."""
        pygame.display.set_caption("Checkers (Draughts)")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self._initialize_fonts()
        self._initialize_game_state()
        self._initialize_ui()

    def _initialize_fonts(self) -> None:
        """Initialize all font objects used in the application."""
        self.font_small = pygame.font.SysFont("arial", FONT_SIZE_SMALL)
        self.font_medium = pygame.font.SysFont("arial", FONT_SIZE_MEDIUM, bold=True)
        self.font_large = pygame.font.SysFont("arial", FONT_SIZE_LARGE, bold=True)

    def _initialize_game_state(self) -> None:
        """Initialize the board and game state."""
        self.board = Board()
        self.state = GameState(self.board)

    def _initialize_ui(self) -> None:
        """Initialize UI components and status tracking."""
        self.input_box = InputBox(
            INPUT_BOX_X,
            BOARD_SIZE + INPUT_BOX_Y_OFFSET,
            WIDTH - INPUT_BOX_WIDTH_MARGIN,
            INPUT_BOX_HEIGHT,
            self.font_medium,
            placeholder="Enter move (e.g., b6-c5 or c3:e5:g7), Enter to submit"
        )
        self.status_message = INITIAL_STATUS_MESSAGE
        self.status_color = STATUS_OK_COLOR
        self.running = True

    def reset(self) -> None:
        """Reset the game to initial state."""
        self._initialize_game_state()
        self._set_status(NEW_GAME_MESSAGE, error=False)
        logger.info("Game reset")

    def run(self) -> None:
        """Execute the main game loop."""
        while self.running:
            self._handle_events()
            self.draw()
            self.clock.tick(FPS)

    def _handle_events(self) -> None:
        """Process all pygame events."""
        for event in pygame.event.get():
            self._handle_quit_event(event)
            self._handle_keyboard_event(event)
            self._handle_input_box_event(event)

    def _handle_quit_event(self, event: pygame.event.EventType) -> None:
        """
        Handle quit event.
        
        Args:
            event: The pygame event to check.
        """
        if event.type == pygame.QUIT:
            self.running = False

    def _handle_keyboard_event(self, event: pygame.event.EventType) -> None:
        """
        Handle keyboard events for game controls.
        
        Args:
            event: The pygame event to check.
        """
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_r:
            self.reset()
        elif event.key == pygame.K_h:
            self._show_help()

    def _handle_input_box_event(self, event: pygame.event.EventType) -> None:
        """
        Handle input box events and process move submissions.
        
        Args:
            event: The pygame event to pass to the input box.
        """
        submit = self.input_box.handle_event(event)
        if submit is not None:
            text = submit.strip()
            if text:
                self.handle_move_input(text)

    def _show_help(self) -> None:
        """Display help information to the console."""
        for line in HELP_TEXT:
            logger.info(line)

    def handle_move_input(self, text: str) -> None:
        """
        Parse and process a move input from the user.
        
        Args:
            text: The raw move input string from the user.
        """
        try:
            seq = MoveParser.parse(text)
        except MoveParseError as e:
            self._set_status(PARSE_ERROR_MESSAGE.format(e), error=True)
            return

        # Validate and attempt to apply the move
        ok, msg = self.state.try_move(seq)
        if ok:
            self._handle_successful_move(msg)
        else:
            self._set_status(msg or ILLEGAL_MOVE_MESSAGE, error=True)

    def _handle_successful_move(self, msg: str) -> None:
        """
        Handle the result of a successful move.
        
        Args:
            msg: The message from the move validation.
        """
        next_player = self._get_next_player_name()
        self._set_status(msg or MOVE_ACCEPTED_MESSAGE.format(next_player), error=False)

        # Check for game over condition
        over, winner, reason = self.state.is_game_over()
        if over:
            self._handle_game_over(winner, reason)

    def _handle_game_over(self, winner: str | None, reason: str) -> None:
        """
        Handle game over state.
        
        Args:
            winner: The winning player name, or None for a draw.
            reason: The reason the game ended.
        """
        if winner:
            message = GAME_OVER_WIN_MESSAGE.format(winner.capitalize(), reason)
        else:
            message = GAME_OVER_DRAW_MESSAGE.format(reason)
        self._set_status(message, error=False)
        logger.info(f"Game over: {message}")

    def _get_next_player_name(self) -> str:
        """
        Get the name of the current player.
        
        Returns:
            The capitalized name of the current player.
        """
        return "Black" if self.state.current_player == "black" else "Red"

    def _set_status(self, msg: str, error: bool = False) -> None:
        """
        Update the status message and color.
        
        Args:
            msg: The status message to display.
            error: Whether this is an error message.
        """
        self.status_message = msg
        self.status_color = STATUS_ERR_COLOR if error else STATUS_OK_COLOR

    def draw(self) -> None:
        """Render the game board, UI elements, and status information."""
        self.screen.fill(BG_COLOR)

        # Draw board and pieces
        self.board.draw(self.screen, self.font_medium, last_move=self.state.last_move)

        # Draw bottom panel
        self._draw_panel()

        # Draw UI elements
        self._draw_turn_indicator()
        self._draw_status_message()
        self._draw_instructions()
        self.input_box.draw(self.screen)

        pygame.display.flip()

    def _draw_panel(self) -> None:
        """Draw the bottom control panel background."""
        panel_rect = pygame.Rect(0, BOARD_SIZE, WIDTH, PANEL_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, panel_rect)

    def _draw_turn_indicator(self) -> None:
        """Draw the current player turn indicator."""
        turn_text = f"Turn: {self._get_next_player_name()}"
        turn_surf = self.font_medium.render(turn_text, True, TEXT_COLOR)
        self.screen.blit(turn_surf, (INPUT_BOX_X, BOARD_SIZE - TURN_LABEL_Y_OFFSET))

    def _draw_status_message(self) -> None:
        """Draw the status message with appropriate color."""
        status_surf = self.font_small.render(self.status_message, True, self.status_color)
        self.screen.blit(status_surf, (INPUT_BOX_X, BOARD_SIZE + STATUS_LABEL_Y_OFFSET))

    def _draw_instructions(self) -> None:
        """Draw the instructions text at the bottom of the panel."""
        text_surf = self.font_small.render(INSTRUCTIONS_TEXT, True, INFO_TEXT_COLOR)
        self.screen.blit(text_surf, (INPUT_BOX_X, BOARD_SIZE + PANEL_HEIGHT - INSTRUCTIONS_Y_OFFSET))