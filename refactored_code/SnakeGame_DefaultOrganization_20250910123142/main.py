import sys
import logging
import pygame
from settings import WIDTH, HEIGHT, BG_COLOR, TITLE, DIFFICULTY_SPEEDS
from ui import Button, draw_text
from game import Game

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# UI Constants
BUTTON_WIDTH = 240
BUTTON_HEIGHT = 54
BUTTON_SPACING = 16
TITLE_FONT_SIZE = 48
BUTTON_FONT_SIZE = 28
HINT_FONT_SIZE = 18
TITLE_OFFSET_Y = 60
HINT_OFFSET_Y = 40
FPS = 60
ICON_SIZE = 32

# Color Constants
BUTTON_BASE_COLOR = (40, 40, 40)
BUTTON_HOVER_COLOR = (70, 70, 70)
BUTTON_TEXT_COLOR = (255, 255, 255)
TITLE_COLOR = (255, 255, 255)
HINT_COLOR = (200, 200, 200)
ICON_COLOR = (100, 200, 100)

# Keyboard Constants
KEYBOARD_SHORTCUT_START = pygame.K_1
KEYBOARD_SHORTCUT_END = pygame.K_9


def _create_fonts():
    """
    Creates and returns font objects for UI elements.
    
    Returns:
        tuple: (title_font, button_font, hint_font)
    """
    title_font = pygame.font.SysFont("arial", TITLE_FONT_SIZE, bold=True)
    button_font = pygame.font.SysFont("arial", BUTTON_FONT_SIZE, bold=True)
    hint_font = pygame.font.SysFont("arial", HINT_FONT_SIZE)
    return title_font, button_font, hint_font


def _calculate_button_positions(num_buttons):
    """
    Calculates the starting Y position for vertically centered buttons.
    
    Args:
        num_buttons (int): Number of buttons to position
        
    Returns:
        int: Starting Y coordinate for the first button
    """
    total_height = num_buttons * BUTTON_HEIGHT + (num_buttons - 1) * BUTTON_SPACING
    return HEIGHT // 2 - total_height // 2


def _create_difficulty_buttons(difficulties, button_font, start_y):
    """
    Creates button objects for each difficulty level.
    
    Args:
        difficulties (list): List of difficulty names
        button_font (pygame.font.Font): Font for button text
        start_y (int): Starting Y coordinate for buttons
        
    Returns:
        list: List of Button objects
    """
    buttons = []
    for i, difficulty_name in enumerate(difficulties):
        button_rect = pygame.Rect(
            (WIDTH - BUTTON_WIDTH) // 2,
            start_y + i * (BUTTON_HEIGHT + BUTTON_SPACING),
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
        )
        button = Button(
            button_rect,
            f"{i + 1}. {difficulty_name}",
            button_font,
            base_color=BUTTON_BASE_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            text_color=BUTTON_TEXT_COLOR,
        )
        buttons.append(button)
    return buttons


def _handle_keyboard_input(event, difficulties):
    """
    Handles keyboard input for difficulty selection.
    
    Args:
        event (pygame.event.EventType): The keyboard event
        difficulties (list): List of available difficulties
        
    Returns:
        str or None: Selected difficulty name or None if quit/escape pressed
    """
    if event.key in (pygame.K_ESCAPE, pygame.K_q):
        return None
    
    # Handle keyboard shortcuts 1-9 for difficulty selection
    if KEYBOARD_SHORTCUT_START <= event.key <= KEYBOARD_SHORTCUT_END:
        difficulty_index = event.key - KEYBOARD_SHORTCUT_START
        if 0 <= difficulty_index < len(difficulties):
            return difficulties[difficulty_index]
    
    return "no_selection"


def _handle_mouse_input(event, buttons, difficulties):
    """
    Handles mouse input for button clicks.
    
    Args:
        event (pygame.event.EventType): The mouse event
        buttons (list): List of Button objects
        difficulties (list): List of difficulty names
        
    Returns:
        str or None: Selected difficulty name or "no_selection" if no button clicked
    """
    mouse_position = pygame.mouse.get_pos()
    for button, difficulty_name in zip(buttons, difficulties):
        if button.was_clicked(event, mouse_position):
            return difficulty_name
    return "no_selection"


def _draw_difficulty_menu(screen, title_font, hint_font, buttons, start_y):
    """
    Renders the difficulty selection menu on screen.
    
    Args:
        screen (pygame.Surface): The display surface
        title_font (pygame.font.Font): Font for the title
        hint_font (pygame.font.Font): Font for hint text
        buttons (list): List of Button objects to draw
        start_y (int): Y coordinate where buttons start
    """
    screen.fill(BG_COLOR)
    
    # Draw title
    draw_text(
        screen,
        "Snake by ChatDev",
        title_font,
        TITLE_COLOR,
        (WIDTH // 2, start_y - TITLE_OFFSET_Y),
    )
    
    # Draw difficulty buttons
    for button in buttons:
        button.draw(screen)
    
    # Draw hint text
    draw_text(
        screen,
        "Click or press 1-4 to choose difficulty. ESC to quit.",
        hint_font,
        HINT_COLOR,
        (WIDTH // 2, HEIGHT - HINT_OFFSET_Y),
    )
    
    pygame.display.flip()


def choose_difficulty(screen):
    """
    Displays a difficulty selection menu and returns the chosen difficulty.
    
    Allows user to select difficulty via mouse clicks or keyboard shortcuts (1-9).
    Returns None if user quits or presses ESC.
    
    Args:
        screen (pygame.Surface): The display surface
        
    Returns:
        str or None: Selected difficulty name or None if user quits
    """
    pygame.display.set_caption(f"{TITLE} - Select Difficulty")
    clock = pygame.time.Clock()
    
    title_font, button_font, hint_font = _create_fonts()
    
    difficulties = list(DIFFICULTY_SPEEDS.keys())
    start_y = _calculate_button_positions(len(difficulties))
    buttons = _create_difficulty_buttons(difficulties, button_font, start_y)
    
    while True:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            if event.type == pygame.KEYDOWN:
                result = _handle_keyboard_input(event, difficulties)
                if result is not None:
                    return result
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                result = _handle_mouse_input(event, buttons, difficulties)
                if result != "no_selection":
                    return result
        
        _draw_difficulty_menu(screen, title_font, hint_font, buttons, start_y)


def _initialize_pygame():
    """
    Initializes Pygame and creates the game window.
    
    Returns:
        pygame.Surface: The display surface
    """
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    
    # Create and set window icon
    icon_surface = pygame.Surface((ICON_SIZE, ICON_SIZE))
    icon_surface.fill(ICON_COLOR)
    pygame.display.set_icon(icon_surface)
    
    logger.info("Pygame initialized successfully")
    return screen


def _run_game_loop(screen):
    """
    Runs the main game loop with difficulty selection and game execution.
    
    Args:
        screen (pygame.Surface): The display surface
    """
    while True:
        difficulty = choose_difficulty(screen)
        if difficulty is None:
            logger.info("User quit from difficulty selection menu")
            break
        
        logger.info(f"Starting game with difficulty: {difficulty}")
        game = Game(screen, difficulty)
        next_state = game.run()
        
        if next_state == "quit":
            logger.info("User quit from game")
            break
        # If "menu", loop back to difficulty selection


def main():
    """
    Main entry point for the Snake game application.
    
    Initializes Pygame, displays the difficulty selection menu,
    and runs the game loop.
    """
    try:
        screen = _initialize_pygame()
        _run_game_loop(screen)
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()