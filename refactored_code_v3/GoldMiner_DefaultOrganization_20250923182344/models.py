import logging
import math
from typing import List, Optional, Dict

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

# Claw swing parameters
CLAW_ANGLE_MIN = -65.0
CLAW_ANGLE_MAX = 65.0
CLAW_SWING_SPEED = 65.0  # degrees per second
CLAW_SWING_DIR_RIGHT = 1.0
CLAW_SWING_DIR_LEFT = -1.0

# Claw rope parameters
CLAW_ROPE_MIN = 30.0
CLAW_ROPE_MAX_BASE = 120.0
CLAW_ROPE_EXTEND_SPEED = 360.0  # pixels per second
CLAW_ROPE_RETRACT_BASE_SPEED = 320.0  # pixels per second
CLAW_ROPE_RETRACT_MIN_SPEED = 60.0  # minimum retraction speed for heavy objects

# Claw state machine states
CLAW_STATE_SWING = "swing"
CLAW_STATE_EXTEND = "extend"
CLAW_STATE_RETRACT = "retract"

# Object constraints
MIN_OBJECT_WEIGHT = 0.1
MAX_DEPTH_BUFFER = 10.0

# Event types
EVENT_TYPE_COLLECT = "collect"


# ============================================================================
# Utility Functions
# ============================================================================

def clamp(value: float, lower_bound: float, upper_bound: float) -> float:
    """
    Clamp a value between lower and upper bounds.
    
    Args:
        value: The value to clamp.
        lower_bound: The minimum allowed value.
        upper_bound: The maximum allowed value.
    
    Returns:
        The clamped value.
    """
    return max(lower_bound, min(upper_bound, value))


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculate Euclidean distance between two points.
    
    Args:
        x1: X coordinate of first point.
        y1: Y coordinate of first point.
        x2: X coordinate of second point.
        y2: Y coordinate of second point.
    
    Returns:
        The Euclidean distance between the two points.
    """
    delta_x = x2 - x1
    delta_y = y2 - y1
    return math.sqrt(delta_x * delta_x + delta_y * delta_y)


# ============================================================================
# Game Entities
# ============================================================================

class MineObject:
    """
    Represents a collectible object in the mine.
    
    Attributes:
        x: X coordinate of the object center.
        y: Y coordinate of the object center.
        r: Radius of the object.
        kind: Type/name of the object.
        value: Point value when collected.
        weight: Weight affecting retraction speed.
        color: Display color of the object.
        collected: Whether the object has been collected.
    """

    def __init__(
        self,
        x: float,
        y: float,
        r: float,
        kind: str,
        value: int,
        weight: float,
        color: str,
    ):
        """
        Initialize a mine object.
        
        Args:
            x: X coordinate of the object center.
            y: Y coordinate of the object center.
            r: Radius of the object.
            kind: Type/name of the object.
            value: Point value when collected.
            weight: Weight of the object (clamped to minimum).
            color: Display color of the object.
        """
        self.x = x
        self.y = y
        self.r = r
        self.kind = kind
        self.value = value
        self.weight = max(MIN_OBJECT_WEIGHT, float(weight))
        self.color = color
        self.collected = False

    def __repr__(self) -> str:
        """Return a string representation of the mine object."""
        return (
            f"<MineObject {self.kind} (${self.value}) "
            f"@({self.x:.1f},{self.y:.1f}) r={self.r}>"
        )


class Claw:
    """
    Represents the claw mechanism for collecting objects.
    
    The claw operates in three states:
    - swing: Oscillates left and right at the anchor point.
    - extend: Extends the rope downward to search for objects.
    - retract: Retracts the rope, pulling any attached object upward.
    
    Attributes:
        anchor_x: X coordinate of the claw anchor point.
        anchor_y: Y coordinate of the claw anchor point.
        angle_deg: Current swing angle in degrees.
        rope_length: Current length of the extended rope.
        state: Current state of the claw ("swing", "extend", or "retract").
        attached: The object currently attached to the claw, if any.
    """

    def __init__(self, anchor_x: float, anchor_y: float, max_depth_y: float):
        """
        Initialize the claw.
        
        Args:
            anchor_x: X coordinate of the anchor point.
            anchor_y: Y coordinate of the anchor point.
            max_depth_y: Maximum Y coordinate (bottom of play area).
        """
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y

        # Swing parameters
        self.angle_deg = 0.0
        self.angle_min = CLAW_ANGLE_MIN
        self.angle_max = CLAW_ANGLE_MAX
        self.swing_speed = CLAW_SWING_SPEED
        self.swing_dir = CLAW_SWING_DIR_RIGHT

        # Rope parameters
        self.rope_length = CLAW_ROPE_MIN
        self.rope_min = CLAW_ROPE_MIN
        # Calculate maximum rope length based on play area depth
        self.rope_max = max(
            CLAW_ROPE_MAX_BASE,
            max_depth_y - anchor_y - MAX_DEPTH_BUFFER,
        )
        self.extend_speed = CLAW_ROPE_EXTEND_SPEED
        self.retract_base_speed = CLAW_ROPE_RETRACT_BASE_SPEED

        # State machine
        self.state = CLAW_STATE_SWING
        self.attached: Optional[MineObject] = None

    def reset(self) -> None:
        """Reset the claw to its initial state."""
        self.angle_deg = 0.0
        self.swing_dir = CLAW_SWING_DIR_RIGHT
        self.rope_length = self.rope_min
        self.state = CLAW_STATE_SWING
        self.attached = None

    def start_grab(self) -> None:
        """Initiate a grab attempt if the claw is in swing state."""
        if self.state == CLAW_STATE_SWING:
            self.state = CLAW_STATE_EXTEND

    def hook_position(self) -> tuple[float, float]:
        """
        Calculate the current position of the hook at the end of the rope.
        
        Returns:
            A tuple (x, y) representing the hook position.
        """
        angle_radians = math.radians(self.angle_deg)
        hook_x = self.anchor_x + math.cos(angle_radians) * self.rope_length
        hook_y = self.anchor_y + math.sin(angle_radians) * self.rope_length
        return hook_x, hook_y

    def _attach(self, obj: MineObject) -> None:
        """
        Attach an object to the claw.
        
        Args:
            obj: The object to attach.
        """
        self.attached = obj
        logger.debug(f"Claw attached to {obj.kind}")

    def _release(self) -> None:
        """Release the currently attached object."""
        if self.attached is not None:
            logger.debug(f"Claw released {self.attached.kind}")
        self.attached = None

    def _update_swing(self, dt: float) -> None:
        """
        Update the claw swing angle.
        
        Args:
            dt: Delta time in seconds.
        """
        # Update angle based on swing direction and speed
        self.angle_deg += self.swing_speed * self.swing_dir * dt

        # Clamp angle and reverse direction at limits
        if self.angle_deg >= self.angle_max:
            self.angle_deg = self.angle_max
            self.swing_dir = CLAW_SWING_DIR_LEFT
        elif self.angle_deg <= self.angle_min:
            self.angle_deg = self.angle_min
            self.swing_dir = CLAW_SWING_DIR_RIGHT

        # Rope stays at minimum during swing
        self.rope_length = self.rope_min

    def _update_extend(
        self,
        dt: float,
        objects: List[MineObject],
        hook_radius: float,
    ) -> Optional[MineObject]:
        """
        Update the claw extension phase.
        
        Args:
            dt: Delta time in seconds.
            objects: List of objects in the play area.
            hook_radius: Radius of the hook for collision detection.
        
        Returns:
            The object that was hit, or None if no collision.
        """
        # Extend the rope
        self.rope_length += self.extend_speed * dt
        hook_x, hook_y = self.hook_position()

        # Check for collision with objects
        hit_object = self._find_collision(hook_x, hook_y, hook_radius, objects)

        if hit_object is not None:
            self._attach(hit_object)
            self.state = CLAW_STATE_RETRACT
            return hit_object

        # Check if we've reached maximum extension
        max_depth_reached = (
            self.rope_length >= self.rope_max
            or hook_y >= (self.anchor_y + self.rope_max - MAX_DEPTH_BUFFER)
        )
        if max_depth_reached:
            self.state = CLAW_STATE_RETRACT

        return None

    def _update_retract(self, dt: float) -> Optional[Dict]:
        """
        Update the claw retraction phase.
        
        Args:
            dt: Delta time in seconds.
        
        Returns:
            An event dict if an object was collected, None otherwise.
        """
        # Calculate retraction speed based on attached object weight
        retraction_speed = self._calculate_retraction_speed()
        self.rope_length -= retraction_speed * dt

        # Move attached object with the hook
        if self.attached is not None:
            hook_x, hook_y = self.hook_position()
            self.attached.x = hook_x
            self.attached.y = hook_y

        # Check if retraction is complete
        if self.rope_length <= self.rope_min:
            self.rope_length = self.rope_min
            event = self._finalize_collection()
            self.state = CLAW_STATE_SWING
            return event

        return None

    def _calculate_retraction_speed(self) -> float:
        """
        Calculate the rope retraction speed based on attached object weight.
        
        Returns:
            The retraction speed in pixels per second.
        """
        if self.attached is None:
            return self.retract_base_speed

        # Heavier objects reel in slower
        weight_factor = float(self.attached.weight)
        return max(
            CLAW_ROPE_RETRACT_MIN_SPEED,
            self.retract_base_speed / weight_factor,
        )

    def _find_collision(
        self,
        hook_x: float,
        hook_y: float,
        hook_radius: float,
        objects: List[MineObject],
    ) -> Optional[MineObject]:
        """
        Find the first object colliding with the hook.
        
        Args:
            hook_x: X coordinate of the hook.
            hook_y: Y coordinate of the hook.
            hook_radius: Radius of the hook.
            objects: List of objects to check.
        
        Returns:
            The first object that collides with the hook, or None.
        """
        for obj in objects:
            if obj.collected:
                continue
            collision_distance = hook_radius + obj.r
            if distance(hook_x, hook_y, obj.x, obj.y) <= collision_distance:
                return obj
        return None

    def _finalize_collection(self) -> Optional[Dict]:
        """
        Finalize the collection of an attached object.
        
        Returns:
            An event dict if an object was collected, None otherwise.
        """
        event = None
        if self.attached is not None:
            self.attached.collected = True
            event = {EVENT_TYPE_COLLECT: EVENT_TYPE_COLLECT, "object": self.attached}
            logger.info(f"Collected {self.attached.kind} worth ${self.attached.value}")
        self._release()
        return event

    def update(
        self,
        dt: float,
        objects: List[MineObject],
        hook_radius: float,
    ) -> Optional[Dict]:
        """
        Update claw physics and handle grabbing logic.
        
        Args:
            dt: Delta time in seconds.
            objects: List of objects in the play area.
            hook_radius: Radius of the hook for collision detection.
        
        Returns:
            An event dict when an object is collected:
            {"type": "collect", "object": obj}, or None.
        """
        event = None

        try:
            if self.state == CLAW_STATE_SWING:
                self._update_swing(dt)
            elif self.state == CLAW_STATE_EXTEND:
                self._update_extend(dt, objects, hook_radius)
            elif self.state == CLAW_STATE_RETRACT:
                event = self._update_retract(dt)
        except (ValueError, TypeError) as e:
            logger.error(f"Error updating claw: {e}")

        return event