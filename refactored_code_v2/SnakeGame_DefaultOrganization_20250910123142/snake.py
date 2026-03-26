import logging
from collections import deque

# Configure logging
logger = logging.getLogger(__name__)

# Constants
INITIAL_SNAKE_LENGTH = 3
INITIAL_DIRECTION = (1, 0)  # Moving right
DIRECTION_UP = (0, -1)
DIRECTION_DOWN = (0, 1)
DIRECTION_LEFT = (-1, 0)
DIRECTION_RIGHT = (1, 0)


class Snake:
    """
    Represents the snake on a grid.
    
    The snake is a deque of (x, y) positions where the rightmost element
    is the head and the leftmost is the tail. Direction is represented as
    a (dx, dy) tuple indicating movement per step.
    """

    def __init__(self, start_pos):
        """
        Initialize a snake with the given starting head position.
        
        Args:
            start_pos: Tuple of (x, y) coordinates for the initial head position.
                      The snake starts with length 3 moving to the right.
        """
        x, y = start_pos
        self.body = deque()
        self._initialize_body(x, y)
        self.direction = INITIAL_DIRECTION
        logger.debug(f"Snake initialized at position {start_pos}")

    def _initialize_body(self, head_x, head_y):
        """
        Initialize the snake body with three segments.
        
        Args:
            head_x: X coordinate of the head.
            head_y: Y coordinate of the head.
        """
        # Create body segments from tail to head (left to right)
        for offset in range(INITIAL_SNAKE_LENGTH - 1, -1, -1):
            self.body.append((head_x - offset, head_y))

    @property
    def head(self):
        """
        Get the head position of the snake.
        
        Returns:
            Tuple of (x, y) representing the head position.
        """
        return self.body[-1]

    def set_direction(self, new_direction):
        """
        Set the snake's direction if the move is valid.
        
        Prevents the snake from reversing into itself and ignores no-op
        direction changes.
        
        Args:
            new_direction: Tuple of (dx, dy) representing the new direction.
        """
        if self._is_reverse_direction(new_direction):
            logger.debug(f"Ignored reverse direction: {new_direction}")
            return
        
        if self._is_same_direction(new_direction):
            return
        
        self.direction = new_direction
        logger.debug(f"Direction changed to {new_direction}")

    def _is_reverse_direction(self, new_direction):
        """
        Check if the new direction is a 180-degree reversal of current direction.
        
        Args:
            new_direction: Tuple of (dx, dy) to check.
            
        Returns:
            True if new_direction reverses the current direction and snake length > 1.
        """
        if len(self.body) <= 1:
            return False
        
        current_dx, current_dy = self.direction
        new_dx, new_dy = new_direction
        
        # Reverse occurs when new direction is opposite to current
        return current_dx == -new_dx and current_dy == -new_dy

    def _is_same_direction(self, new_direction):
        """
        Check if the new direction is the same as the current direction.
        
        Args:
            new_direction: Tuple of (dx, dy) to check.
            
        Returns:
            True if new_direction matches the current direction.
        """
        current_dx, current_dy = self.direction
        new_dx, new_dy = new_direction
        return current_dx == new_dx and current_dy == new_dy

    def move(self, grow=False):
        """
        Move the snake one cell in the current direction.
        
        Args:
            grow: If True, the snake grows by one segment. If False, the tail
                  is removed, maintaining the current length.
        
        Returns:
            Tuple of (x, y) representing the new head position.
        """
        new_head = self._calculate_new_head()
        self.body.append(new_head)
        
        if not grow:
            self.body.popleft()
        
        logger.debug(f"Snake moved to {new_head}, grow={grow}")
        return new_head

    def _calculate_new_head(self):
        """
        Calculate the new head position based on current head and direction.
        
        Returns:
            Tuple of (x, y) representing the new head position.
        """
        head_x, head_y = self.head
        direction_x, direction_y = self.direction
        return (head_x + direction_x, head_y + direction_y)

    def collides_with_self(self):
        """
        Check if the snake's head collides with its body.
        
        Returns:
            True if the head position matches any body segment except the head itself.
        """
        head = self.head
        # Check all body segments except the head (last element)
        body_without_head = list(self.body)[:-1]
        
        for segment in body_without_head:
            if segment == head:
                logger.debug("Self-collision detected")
                return True
        
        return False