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
ROPE_BUFFER_DISTANCE = 10.0

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
        The distance between the two points.
    """
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)


# ============================================================================
# Classes
# ============================================================================

class MineObject:
    """
    Represents a collectible object in the mining game.
    
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
        Initialize a MineObject.
        
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
        """Return a string representation of the MineObject."""
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
        attached: The MineObject currently attached to the claw, if any.
    """

    def __init__(self, anchor_x: float, anchor_y: float, max_depth_y: float):
        """
        Initialize the Claw.
        
        Args:
            anchor_x: X coordinate of the anchor point.
            anchor_y: Y coordinate of the anchor point.
            max_depth_y: Maximum Y coordinate the rope can reach.
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
        self.rope_max = max(
            CLAW_ROPE_MAX_BASE,
            max_depth_y - anchor_y - ROPE_BUFFER_DISTANCE,
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
            obj: The MineObject to attach.
        """
        self.attached = obj
        logger.debug(f"Claw attached to {obj}")

    def _release(self) -> None:
        """Release the currently attached object."""
        if self.attached is not None:
            logger.debug(f"Claw released {self.attached}")
        self.attached = None

    def _update_swing(self, dt: float) -> None:
        """
        Update the claw swing angle.
        
        Args:
            dt: Delta time in seconds.
        """
        self.angle_deg += self.swing_speed * self.swing_dir * dt

        # Clamp angle and reverse direction at bounds
        if self.angle_deg >= self.angle_max:
            self.angle_deg = self.angle_max
            self.swing_dir = CLAW_SWING_DIR_LEFT
        elif self.angle_deg <= self.angle_min:
            self.angle_deg = self.angle_min
            self.swing_dir = CLAW_SWING_DIR_RIGHT

        self.rope_length = self.rope_min

    def _find_collision(
        self, hook_x: float, hook_y: float, hook_radius: float, objects: List[MineObject]
    ) -> Optional[MineObject]:
        """
        Check if the hook collides with any uncollected object.
        
        Args:
            hook_x: X coordinate of the hook.
            hook_y: Y coordinate of the hook.
            hook_radius: Radius of the hook for collision detection.
            objects: List of MineObjects to check against.
        
        Returns:
            The first MineObject that collides with the hook, or None.
        """
        for obj in objects:
            if obj.collected:
                continue
            collision_distance = hook_radius + obj.r
            if distance(hook_x, hook_y, obj.x, obj.y) <= collision_distance:
                return obj
        return None

    def _update_extend(
        self, dt: float, objects: List[MineObject], hook_radius: float
    ) -> bool:
        """
        Update the claw rope extension phase.
        
        Args:
            dt: Delta time in seconds.
            objects: List of MineObjects to check for collisions.
            hook_radius: Radius of the hook for collision detection.
        
        Returns:
            True if an object was attached, False otherwise.
        """
        self.rope_length += self.extend_speed * dt
        hook_x, hook_y = self.hook_position()

        # Check for collision with objects
        hit_obj = self._find_collision(hook_x, hook_y, hook_radius, objects)
        if hit_obj is not None:
            self._attach(hit_obj)
            self.state = CLAW_STATE_RETRACT
            return True

        # Check if rope has reached maximum extension
        max_depth_reached = self.rope_length >= self.rope_max
        below_max_y = hook_y >= (self.anchor_y + self.rope_max - ROPE_BUFFER_DISTANCE)
        if max_depth_reached or below_max_y:
            self.state = CLAW_STATE_RETRACT

        return False

    def _calculate_retract_speed(self) -> float:
        """
        Calculate the rope retraction speed based on attached object weight.
        
        Returns:
            The retraction speed in pixels per second.
        """
        if self.attached is None:
            return self.retract_base_speed

        # Heavier objects reel in slower
        weight_adjusted_speed = self.retract_base_speed / float(self.attached.weight)
        return max(CLAW_ROPE_RETRACT_MIN_SPEED, weight_adjusted_speed)

    def _update_retract(self, dt: float) -> Optional[Dict]:
        """
        Update the claw rope retraction phase.
        
        Args:
            dt: Delta time in seconds.
        
        Returns:
            An event dict if an object was collected, None otherwise.
        """
        retract_speed = self._calculate_retract_speed()
        self.rope_length -= retract_speed * dt

        # Move attached object with the hook
        hook_x, hook_y = self.hook_position()
        if self.attached is not None:
            self.attached.x = hook_x
            self.attached.y = hook_y

        # Check if retraction is complete
        if self.rope_length <= self.rope_min:
            self.rope_length = self.rope_min
            event = None

            # Collect the attached object if present
            if self.attached is not None:
                self.attached.collected = True
                event = {EVENT_TYPE_COLLECT: EVENT_TYPE_COLLECT, "object": self.attached}
                logger.info(f"Collected {self.attached}")

            # Return to swinging state
            self._release()
            self.state = CLAW_STATE_SWING
            return event

        return None

    def update(
        self, dt: float, objects: List[MineObject], hook_radius: float
    ) -> Optional[Dict]:
        """
        Update claw physics and handle grabbing logic.
        
        Args:
            dt: Delta time in seconds.
            objects: List of MineObjects in the game.
            hook_radius: Radius of the hook for collision detection.
        
        Returns:
            An event dict when an object is collected:
            {"type": "collect", "object": obj}, or None if no collection occurred.
        """
        event = None

        if self.state == CLAW_STATE_SWING:
            self._update_swing(dt)
        elif self.state == CLAW_STATE_EXTEND:
            self._update_extend(dt, objects, hook_radius)
        elif self.state == CLAW_STATE_RETRACT:
            event = self._update_retract(dt)

        return event