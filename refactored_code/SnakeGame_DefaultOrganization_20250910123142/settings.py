'''
Global configuration and constants for the Snake game.
'''

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Grid and sizing constants
CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 30
WIDTH = CELL_SIZE * GRID_WIDTH
HEIGHT = CELL_SIZE * GRID_HEIGHT

# Color constants (RGB tuples)
class Colors:
    """RGB color definitions for game elements."""
    BACKGROUND = (18, 18, 18)
    GRID = (36, 36, 36)
    SNAKE_HEAD = (0, 200, 0)
    SNAKE_BODY = (0, 150, 0)
    FOOD = (220, 60, 60)
    TEXT = (255, 255, 255)
    TEXT_SHADOW = (0, 0, 0)


# Game metadata
GAME_TITLE = "Snake by ChatDev"

# Difficulty settings mapping difficulty levels to game speed (moves per second)
DIFFICULTY_SPEEDS = {
    "Easy": 8,
    "Normal": 12,
    "Hard": 16,
    "Insane": 22,
}

# Scoring constants
FOOD_SCORE_VALUE = 1

# Validation constants
MIN_DIFFICULTY = min(DIFFICULTY_SPEEDS.values())
MAX_DIFFICULTY = max(DIFFICULTY_SPEEDS.values())
VALID_DIFFICULTIES = set(DIFFICULTY_SPEEDS.keys())


def get_difficulty_speed(difficulty_level: str) -> int:
    """
    Retrieve the game speed for a given difficulty level.
    
    Args:
        difficulty_level: The difficulty level as a string key.
        
    Returns:
        The speed in moves per second.
        
    Raises:
        ValueError: If the difficulty level is not recognized.
    """
    if difficulty_level not in DIFFICULTY_SPEEDS:
        logger.error(f"Invalid difficulty level: {difficulty_level}")
        raise ValueError(
            f"Difficulty must be one of {VALID_DIFFICULTIES}, "
            f"got '{difficulty_level}'"
        )
    return DIFFICULTY_SPEEDS[difficulty_level]


def validate_grid_dimensions() -> bool:
    """
    Validate that grid dimensions are positive and consistent.
    
    Returns:
        True if dimensions are valid.
        
    Raises:
        ValueError: If any dimension is invalid.
    """
    if CELL_SIZE <= 0:
        logger.error(f"Invalid CELL_SIZE: {CELL_SIZE}")
        raise ValueError("CELL_SIZE must be positive")
    
    if GRID_WIDTH <= 0 or GRID_HEIGHT <= 0:
        logger.error(f"Invalid grid dimensions: {GRID_WIDTH}x{GRID_HEIGHT}")
        raise ValueError("GRID_WIDTH and GRID_HEIGHT must be positive")
    
    if WIDTH != CELL_SIZE * GRID_WIDTH or HEIGHT != CELL_SIZE * GRID_HEIGHT:
        logger.error("Width/Height do not match CELL_SIZE * GRID dimensions")
        raise ValueError("WIDTH and HEIGHT must equal CELL_SIZE * GRID dimensions")
    
    return True
Human: I need to refactor a game engine code. Here's the original code:

```python
import pygame
import random
import sys

pygame.init()

CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 30
WIDTH = CELL_SIZE * GRID_WIDTH
HEIGHT = CELL_SIZE * GRID_HEIGHT

BG_COLOR = (18, 18, 18)
GRID_COLOR = (36, 36, 36)
SNAKE_HEAD_COLOR = (0, 200, 0)
SNAKE_BODY_COLOR = (0, 150, 0)
FOOD_COLOR = (220, 60, 60)
TEXT_COLOR = (255, 255, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()

class Snake:
    def __init__(self):
        self.body = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)

    def move(self):
        head_x, head_y = self.body[0]
        dir_x, dir_y = self.direction
        new_head = (head_x + dir_x, head_y + dir_y)
        self.body.insert(0, new_head)
        self.direction = self.next_direction

    def grow(self):
        pass

    def check_collision(self):
        head = self.body[0]
        if head[0] < 0 or head[0] >= GRID_WIDTH or head[1] < 0 or head[1] >= GRID_HEIGHT:
            return True
        if head in self.body[1:]:
            return True
        return False

    def draw(self, surface):
        for i, segment in enumerate(self.body):
            color = SNAKE_HEAD_COLOR if i == 0 else SNAKE_BODY_COLOR
            pygame.draw.rect(surface, color, (segment[0] * CELL_SIZE, segment[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))

class Food:
    def __init__(self):
        self.position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))

    def draw(self, surface):
        pygame.draw.rect(surface, FOOD_COLOR, (self.position[0] * CELL_SIZE, self.position[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))

class Game:
    def __init__(self):
        self.snake = Snake()
        self.food = Food()
        self.score = 0
        self.running = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and self.snake.direction != (0, 1):
                    self.snake.next_direction = (0, -1)
                if event.key == pygame.K_DOWN and self.snake.direction != (0, -1):
                    self.snake.next_direction = (0, 1)
                if event.key == pygame.K_LEFT and self.snake.direction != (1, 0):
                    self.snake.next_direction = (-1, 0)
                if event.key == pygame.K_RIGHT and self.snake.direction != (-1, 0):
                    self.snake.next_direction = (1, 0)

    def update(self):
        self.snake.move()
        if self.snake.check_collision():
            self.running = False
        if self.snake.body[0] == self.food.position:
            self.score += 1
            self.food = Food()

    def draw(self):
        screen.fill(BG_COLOR)
        self.snake.draw(screen)
        self.food.draw(screen)
        font = pygame.font.Font(None, 36)
        text = font.render(f"Score: {self.score}", True, TEXT_COLOR)
        screen.blit(text, (10, 10))
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(12)

game = Game()
game.run()
pygame.quit()
```

Refactor this code to:
1. Apply DRY — eliminate duplicate logic
2. Break down long functions (>40 lines) into smaller focused ones
3. Add clear docstrings to every function and class
4. Add inline comments for complex logic
5. Replace magic numbers with named constants at the top of the file
6. Replace bare except clauses with specific exception types
7. Replace print() with proper logging
8. Improve variable naming where unclear

IMPORTANT: Return ONLY the refactored Python code. No explanations, no markdown fences, no preamble. Just valid Python.

import logging
import pygame
import random
import sys
from enum import Enum
from typing import Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Pygame
try:
    pygame.init()
except Exception as pygame_error:
    logger.error(f"Failed to initialize Pygame: {pygame_error}")
    sys.exit(1)

# Grid and sizing constants
CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 30
SCREEN_WIDTH = CELL_SIZE * GRID_WIDTH
SCREEN_HEIGHT = CELL_SIZE * GRID_HEIGHT

# Color constants (RGB tuples)
class Colors:
    """RGB color definitions for game elements."""
    BACKGROUND = (18, 18, 18)
    GRID = (36, 36, 36)
    SNAKE_HEAD = (0, 200, 0)
    SNAKE_BODY = (0, 150, 0)
    FOOD = (220, 60, 60)
    TEXT = (255, 255, 255)


# Game configuration constants
GAME_TITLE = "Snake Game"
DEFAULT_GAME_SPEED = 12  # Moves per second
INITIAL_SCORE = 0
FOOD_SCORE_VALUE = 1
FONT_SIZE = 36
SCORE_DISPLAY_OFFSET_X = 10
SCORE_DISPLAY_OFFSET_Y = 10

# Direction vectors for snake movement
class Direction(Enum):
    """Enumeration of valid snake movement directions."""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def is_opposite(self, other: 'Direction') -> bool:
        """
        Check if this direction is opposite to another direction.
        
        Args:
            other: The direction to compare against.
            
        Returns:
            True if directions are opposite, False otherwise.
        """
        opposite_pairs = [
            (Direction.UP, Direction.DOWN),
            (Direction.LEFT, Direction.RIGHT),
        ]
        return (self, other) in opposite_pairs or (other, self) in opposite_pairs


Position = Tuple[int, int]


class Snake:
    """
    Represents the snake entity in the game.
    
    Attributes:
        body: List of positions representing snake segments from head to tail.
        direction: Current movement direction.
        next_direction: Queued direction for next move.
    """

    def __init__(self, start_position: Position = None):
        """
        Initialize the snake at the center of the grid.
        
        Args:
            start_position: Optional starting position for the snake head.
        """
        if start_position is None:
            start_position = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
        
        self.body = [start_position]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        logger.info(f"Snake initialized at position {start_position}")

    def move(self) -> None:
        """
        Move the snake one cell in the current direction.
        
        Updates the snake's body by adding a new head and removing the tail.
        """
        head_x, head_y = self.body[0]
        dir_x, dir_y = self.direction.value
        new_head = (head_x + dir_x, head_y + dir_y)
        
        self.body.insert(0, new_head)
        self.body.pop()  # Remove tail to maintain length
        self.direction = self.next_direction

    def grow(self) -> None:
        """
        Grow the snake by one segment.
        
        Adds a new head without removing the tail, effectively increasing length.
        """
        head_x, head_y = self.body[0]
        dir_x, dir_y = self.direction.value
        new_head = (head_x + dir_x, head_y + dir_y)
        self.body.insert(0, new_head)
        logger.debug(f"Snake grew to length {len(self.body)}")

    def set_direction(self, new_direction: Direction) -> None:
        """
        Set the snake's next direction if it's not opposite to current direction.
        
        Args:
            new_direction: The desired direction to move.
        """
        # Prevent the snake from reversing into itself
        if not self.direction.is_opposite(new_direction):
            self.next_direction = new_direction

    def is_colliding_with_self(self) -> bool:
        """
        Check if the snake's head collides with its body.
        
        Returns:
            True if head collides with body, False otherwise.
        """
        head = self.body[0]
        return head in self.body[1:]

    def is_out_of_bounds(self) -> bool:
        """
        Check if the snake's head is outside the grid boundaries.
        
        Returns:
            True if head is out of bounds, False otherwise.
        """
        head_x, head_y = self.body[0]
        return (head_x < 0 or head_x >= GRID_WIDTH or 
                head_y < 0 or head_y >= GRID_HEIGHT)

    def has_collided(self) -> bool:
        """
        Check if the snake has collided with walls or itself.
        
        Returns:
            True if any collision detected, False otherwise.
        """
        return self.is_out_of_bounds() or self.is_colliding_with_self()

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the snake on the given surface.
        
        Args:
            surface: The pygame surface to draw on.
        """
        for index, segment in enumerate(self.body):
            # Head is drawn in a different color than body segments
            color = Colors.SNAKE_HEAD if index == 0 else Colors.SNAKE_BODY
            rect = pygame.Rect(
                segment[0] * CELL_SIZE,
                segment[1] * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(surface, color, rect)


class Food:
    """
    Represents the food entity in the game.
    
    Attributes:
        position: Current position of the food on the grid.
    """

    def __init__(self):
        """Initialize food at a random position on the grid."""
        self.position = self._generate_random_position()
        logger.debug(f"Food spawned at position {self.position}")

    @staticmethod
    def _generate_random_position() -> Position:
        """
        Generate a random position within the grid boundaries.
        
        Returns:
            A tuple (x, y) representing a random grid position.
        """
        return (
            random.randint(0, GRID_WIDTH - 1),
            random.randint(0, GRID_HEIGHT - 1)
        )

    def respawn(self) -> None:
        """Respawn the food at a new random position."""
        self.position = self._generate_random_position()
        logger.debug(f"Food respawned at position {self.position}")

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the food on the given surface.
        
        Args:
            surface: The pygame surface to draw on.
        """
        rect = pygame.Rect(
            self.position[0] * CELL_SIZE,
            self.position[1] * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        pygame.draw.rect(surface, Colors.FOOD, rect)


class Game:
    """
    Main game controller managing game state and logic.
    
    Attributes:
        snake: The snake entity.
        food: The food entity.
        score: Current game score.
        running: Whether the game