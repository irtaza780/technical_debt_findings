import logging
from dataclasses import dataclass
from typing import Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Movement constants
MIN_COORDINATE = 0
MAX_COORDINATE = 100
MIN_HEALTH = 0


@dataclass
class Entity:
    """Base class for all game entities with position and health."""
    x: int
    y: int
    hp: int

    def __post_init__(self) -> None:
        """Validate entity attributes after initialization."""
        self._validate_position()
        self._validate_health()

    def _validate_position(self) -> None:
        """Validate that position coordinates are within valid bounds."""
        if not (MIN_COORDINATE <= self.x <= MAX_COORDINATE):
            raise ValueError(f"X coordinate {self.x} out of bounds")
        if not (MIN_COORDINATE <= self.y <= MAX_COORDINATE):
            raise ValueError(f"Y coordinate {self.y} out of bounds")

    def _validate_health(self) -> None:
        """Validate that health is non-negative."""
        if self.hp < MIN_HEALTH:
            raise ValueError(f"Health {self.hp} cannot be negative")

    def get_position(self) -> Tuple[int, int]:
        """Return the current position as a tuple.
        
        Returns:
            Tuple[int, int]: A tuple of (x, y) coordinates.
        """
        return (self.x, self.y)

    def set_position(self, x: int, y: int) -> None:
        """Set the entity's position with validation.
        
        Args:
            x: The new x coordinate.
            y: The new y coordinate.
            
        Raises:
            ValueError: If coordinates are out of bounds.
        """
        self.x = x
        self.y = y
        self._validate_position()

    def take_damage(self, damage: int) -> None:
        """Reduce entity health by the specified damage amount.
        
        Args:
            damage: The amount of damage to take.
            
        Raises:
            ValueError: If damage is negative.
        """
        if damage < 0:
            raise ValueError("Damage cannot be negative")
        self.hp = max(MIN_HEALTH, self.hp - damage)
        logger.debug(f"Entity took {damage} damage. Health now: {self.hp}")

    def is_alive(self) -> bool:
        """Check if the entity is still alive.
        
        Returns:
            bool: True if health is greater than 0, False otherwise.
        """
        return self.hp > MIN_HEALTH


@dataclass
class Player(Entity):
    """Represents the player character in the roguelike game.
    
    Inherits position and health from Entity base class.
    """

    def move(self, dx: int, dy: int) -> None:
        """Move the player by the specified delta values.
        
        Args:
            dx: Change in x coordinate.
            dy: Change in y coordinate.
            
        Raises:
            ValueError: If resulting position would be out of bounds.
        """
        new_x = self.x + dx
        new_y = self.y + dy
        try:
            self.set_position(new_x, new_y)
            logger.debug(f"Player moved to ({new_x}, {new_y})")
        except ValueError as e:
            logger.warning(f"Invalid move attempted: {e}")
            raise


@dataclass
class Monster(Entity):
    """Represents a monster enemy in the roguelike game.
    
    Inherits position and health from Entity base class.
    """
    pass