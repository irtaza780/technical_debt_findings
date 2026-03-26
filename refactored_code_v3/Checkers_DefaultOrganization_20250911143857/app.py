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
ILLEGAL_MOVE_MESSAGE = "Illegal move."
MOVE_ACCEPTED_MESSAGE = "Move accepted. {} to move."
GAME_OVER_WITH_WINNER = "Game over: {} wins! ({}) - Press R to restart."
GAME_OVER_DRAW = "Game over: Draw. ({}) - Press R to restart."
INSTRUCTIONS_TEXT = "Type move and press Enter. R: restart, H: help, ESC: quit."
TURN_TEXT = "Turn: {}"

# Help text
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
    
    Manages the game loop, rendering, user input handling, and game state updates.
    """

    def __init__(self):
        """Initialize the Checkers game application with pygame and game state."""
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
        """Initialize UI components including input box and status display."""
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
        logger.info("Game reset to initial state")

    def run(self) -> None:
        """
        Main game loop.
        
        Handles events, updates game state, and renders the display.
        """
        while self.running:
            self._handle_events()
            self.draw()
            self.clock.tick(FPS)

    def _handle_events(self) -> None:
        """Process all pygame events including quit, keyboard, and input box events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            submit = self.input_box.handle_event(event)
            if submit is not None:
                text = submit.strip()
                if text:
                    self.handle_move_input(text)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """
        Handle keyboard input events.
        
        Args:
            event: The pygame KEYDOWN event to process.
        """
        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_r:
            self.reset()
        elif event.key == pygame.K_h:
            self._show_help()

    def _show_help(self) -> None:
        """Display help information to the console."""
        for line in HELP_TEXT:
            logger.info(line)

    def handle_move_input(self, text: str) -> None:
        """
        Parse and process move input from the user.
        
        Validates the move notation, applies it to the game state, and updates
        the status message. Checks for game-over conditions.
        
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
            self._check_game_over()
        else:
            self._set_status(msg or ILLEGAL_MOVE_MESSAGE, error=True)

    def _handle_successful_move(self, msg: str) -> None:
        """
        Handle a successfully executed move.
        
        Args:
            msg: Optional message from the move execution.
        """
        next_player = self._get_player_name(self.state.current_player)
        status = msg or MOVE_ACCEPTED_MESSAGE.format(next_player)
        self._set_status(status, error=False)
        logger.info(f"Move accepted. Next player: {next_player}")

    def _check_game_over(self) -> None:
        """Check if the game is over and update status accordingly."""
        over, winner, reason = self.state.is_game_over()
        if over:
            if winner:
                status = GAME_OVER_WITH_WINNER.format(winner.capitalize(), reason)
            else:
                status = GAME_OVER_DRAW.format(reason)
            self._set_status(status, error=False)
            logger.info(f"Game over: {status}")

    def _set_status(self, msg: str, error: bool = False) -> None:
        """
        Update the status message and color.
        
        Args:
            msg: The status message to display.
            error: Whether this is an error message (True) or success (False).
        """
        self.status_message = msg
        self.status_color = STATUS_ERR_COLOR if error else STATUS_OK_COLOR

    def _get_player_name(self, player: str) -> str:
        """
        Get the display name for a player.
        
        Args:
            player: The player identifier ('red' or 'black').
            
        Returns:
            The capitalized player name.
        """
        return "Red" if player == "red" else "Black"

    def draw(self) -> None:
        """
        Render the entire game display.
        
        Draws the board, pieces, UI elements, and status information.
        """
        self.screen.fill(BG_COLOR)
        self._draw_board()
        self._draw_panel()
        self._draw_turn_indicator()
        self._draw_status_message()
        self.input_box.draw(self.screen)
        pygame.display.flip()

    def _draw_board(self) -> None:
        """Draw the game board and pieces."""
        self.board.draw(self.screen, self.font_medium, last_move=self.state.last_move)

    def _draw_panel(self) -> None:
        """Draw the bottom control panel with instructions."""
        panel_rect = pygame.Rect(0, BOARD_SIZE, WIDTH, PANEL_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, panel_rect)

        instructions = INSTRUCTIONS_TEXT
        text_surf = self.font_small.render(instructions, True, INFO_TEXT_COLOR)
        self.screen.blit(text_surf, (INPUT_BOX_X, BOARD_SIZE + PANEL_HEIGHT - INSTRUCTIONS_Y_OFFSET))

    def _draw_turn_indicator(self) -> None:
        """Draw the current player turn indicator."""
        player_name = self._get_player_name(self.state.current_player)
        turn_text = TURN_TEXT.format(player_name)
        turn_surf = self.font_medium.render(turn_text, True, TEXT_COLOR)
        self.screen.blit(turn_surf, (INPUT_BOX_X, BOARD_SIZE - TURN_LABEL_Y_OFFSET))

    def _draw_status_message(self) -> None:
        """Draw the status message at the bottom of the screen."""
        status_surf = self.font_small.render(self.status_message, True, self.status_color)
        self.screen.blit(status_surf, (INPUT_BOX_X, BOARD_SIZE + STATUS_LABEL_Y_OFFSET))