import logging
from dataclasses import dataclass
from typing import Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Movement constants
MIN_COORDINATE = 0
MAX_COORDINATE = 100
MIN_HP = 0


@dataclass
class Entity:
    """Base class for all entities in the roguelike game.
    
    Attributes:
        x: Horizontal position coordinate.
        y: Vertical position coordinate.
        hp: Health points of the entity.
    """
    x: int
    y: int
    hp: int

    def move(self, delta_x: int, delta_y: int) -> None:
        """Move the entity by the given delta values.
        
        Args:
            delta_x: Change in x coordinate.
            delta_y: Change in y coordinate.
        """
        new_x = self.x + delta_x
        new_y = self.y + delta_y
        
        # Validate coordinates are within bounds
        if self._is_valid_coordinate(new_x) and self._is_valid_coordinate(new_y):
            self.x = new_x
            self.y = new_y
            logger.debug(f"{self.__class__.__name__} moved to ({self.x}, {self.y})")
        else:
            logger.warning(
                f"Invalid move to ({new_x}, {new_y}). "
                f"Coordinates must be between {MIN_COORDINATE} and {MAX_COORDINATE}."
            )

    def take_damage(self, damage: int) -> None:
        """Reduce entity health by the given damage amount.
        
        Args:
            damage: Amount of damage to take.
        """
        if damage < 0:
            logger.warning("Damage cannot be negative. Ignoring.")
            return
        
        self.hp = max(MIN_HP, self.hp - damage)
        logger.debug(f"{self.__class__.__name__} took {damage} damage. HP: {self.hp}")

    def get_position(self) -> Tuple[int, int]:
        """Get the current position of the entity.
        
        Returns:
            Tuple of (x, y) coordinates.
        """
        return (self.x, self.y)

    def is_alive(self) -> bool:
        """Check if the entity is still alive.
        
        Returns:
            True if HP is greater than 0, False otherwise.
        """
        return self.hp > MIN_HP

    @staticmethod
    def _is_valid_coordinate(coordinate: int) -> bool:
        """Validate that a coordinate is within acceptable bounds.
        
        Args:
            coordinate: The coordinate value to validate.
            
        Returns:
            True if coordinate is within bounds, False otherwise.
        """
        return MIN_COORDINATE <= coordinate <= MAX_COORDINATE


@dataclass
class Player(Entity):
    """Player entity in the roguelike game.
    
    Inherits movement and health mechanics from Entity base class.
    """
    pass


@dataclass
class Monster(Entity):
    """Monster entity in the roguelike game.
    
    Inherits movement and health mechanics from Entity base class.
    """
    pass