import logging
import random
import pygame
from settings import FOOD_COLOR, CELL_SIZE

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CELL_SIZE = CELL_SIZE
SPAWN_FAILURE_LOG_LEVEL = logging.WARNING


class Food:
    """
    Represents a food item on the grid.
    
    Manages spawning food at random positions on the grid that are not occupied
    by the snake, and rendering the food on the game surface.
    """

    def __init__(self, grid_width, grid_height, cell_size=DEFAULT_CELL_SIZE):
        """
        Initialize a Food instance.
        
        Args:
            grid_width (int): Width of the game grid in cells.
            grid_height (int): Height of the game grid in cells.
            cell_size (int): Size of each cell in pixels. Defaults to CELL_SIZE.
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.cell_size = cell_size
        self.position = None

    def _get_all_grid_cells(self):
        """
        Generate all possible cell positions on the grid.
        
        Returns:
            set: Set of (x, y) tuples representing all grid cells.
        """
        return {
            (x, y)
            for x in range(self.grid_width)
            for y in range(self.grid_height)
        }

    def _get_free_cells(self, snake_positions):
        """
        Calculate cells that are not occupied by the snake.
        
        Args:
            snake_positions (iterable): Iterable of (x, y) tuples occupied by snake.
        
        Returns:
            list: List of (x, y) tuples representing free cells.
        """
        all_cells = self._get_all_grid_cells()
        occupied_cells = set(snake_positions)
        free_cells = all_cells - occupied_cells
        return list(free_cells)

    def spawn(self, snake_positions):
        """
        Spawn food at a random position not occupied by the snake.
        
        Args:
            snake_positions (iterable): Iterable of (x, y) tuples occupied by snake.
        
        Returns:
            bool: True if food was successfully spawned, False if no free cells available.
        """
        free_cells = self._get_free_cells(snake_positions)
        
        if not free_cells:
            self.position = None
            logger.log(
                SPAWN_FAILURE_LOG_LEVEL,
                "Failed to spawn food: no free cells available on grid"
            )
            return False
        
        self.position = random.choice(free_cells)
        logger.debug(f"Food spawned at position {self.position}")
        return True

    def _get_pixel_rect(self):
        """
        Convert grid position to pixel-based rectangle for rendering.
        
        Returns:
            pygame.Rect: Rectangle in pixel coordinates, or None if position not set.
        """
        if self.position is None:
            return None
        
        grid_x, grid_y = self.position
        pixel_x = grid_x * self.cell_size
        pixel_y = grid_y * self.cell_size
        
        return pygame.Rect(pixel_x, pixel_y, self.cell_size, self.cell_size)

    def draw(self, surface):
        """
        Draw the food as a filled rectangle on the given surface.
        
        Args:
            surface (pygame.Surface): The surface to draw the food on.
        """
        rect = self._get_pixel_rect()
        
        if rect is None:
            return
        
        pygame.draw.rect(surface, FOOD_COLOR, rect)