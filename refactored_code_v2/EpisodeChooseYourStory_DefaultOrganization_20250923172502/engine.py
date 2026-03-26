import logging
from typing import Dict, List, Optional, Any, Set

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_NUMERIC_VALUE = 0
CONDITION_KEYS = {
    "items_have",
    "items_not_have",
    "vars_min",
    "vars_max",
    "vars_eq",
    "relationships_min",
    "flags_set",
    "flags_not_set",
    "visited_nodes_include",
    "visited_nodes_exclude",
}
EFFECT_KEYS = {
    "add_items",
    "remove_items",
    "vars_delta",
    "vars_set",
    "relationships_delta",
    "set_flags",
}


class GameState:
    """
    Tracks items, variables, relationships, flags, and visited nodes.
    """

    def __init__(self):
        """Initialize an empty game state."""
        self.items: Set[str] = set()
        self.variables: Dict[str, int] = {}
        self.relationships: Dict[str, int] = {}
        self.flags: Dict[str, bool] = {}
        self.visited_nodes: List[str] = []

    def add_item(self, item: str) -> None:
        """Add an item to the player's inventory."""
        self.items.add(item)

    def remove_item(self, item: str) -> None:
        """Remove an item from the player's inventory."""
        self.items.discard(item)

    def has_item(self, item: str) -> bool:
        """Check if the player has a specific item."""
        return item in self.items

    def adjust_var(self, name: str, delta: int) -> None:
        """Adjust a variable by a delta amount."""
        self.variables[name] = self.variables.get(name, DEFAULT_NUMERIC_VALUE) + int(delta)

    def set_var(self, name: str, value: int) -> None:
        """Set a variable to a specific value."""
        self.variables[name] = int(value)

    def get_var(self, name: str, default: int = DEFAULT_NUMERIC_VALUE) -> int:
        """Get a variable value with optional default."""
        return self.variables.get(name, default)

    def adjust_relationship(self, name: str, delta: int) -> None:
        """Adjust a relationship value by a delta amount."""
        self.relationships[name] = self.relationships.get(name, DEFAULT_NUMERIC_VALUE) + int(delta)

    def get_relationship(self, name: str, default: int = DEFAULT_NUMERIC_VALUE) -> int:
        """Get a relationship value with optional default."""
        return self.relationships.get(name, default)

    def set_flag(self, name: str, value: bool) -> None:
        """Set a flag to a boolean value."""
        self.flags[name] = bool(value)

    def is_flag(self, name: str) -> bool:
        """Check if a flag is set to True."""
        return bool(self.flags.get(name, False))

    def mark_visited(self, node_id: str) -> None:
        """Mark a node as visited."""
        self.visited_nodes.append(node_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize game state to a dictionary."""
        return {
            "items": sorted(list(self.items)),
            "variables": dict(self.variables),
            "relationships": dict(self.relationships),
            "flags": dict(self.flags),
            "visited_nodes": list(self.visited_nodes),
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Deserialize game state from a dictionary."""
        self.items = set(data.get("items", []))
        self.variables = dict(data.get("variables", {}))
        self.relationships = dict(data.get("relationships", {}))
        self.flags = dict(data.get("flags", {}))
        self.visited_nodes = list(data.get("visited_nodes", []))


def _check_item_conditions(conditions: Dict[str, Any], state: GameState) -> bool:
    """
    Check item-related conditions.

    Args:
        conditions: Dictionary containing items_have and items_not_have keys.
        state: Current game state.

    Returns:
        True if all item conditions are met, False otherwise.
    """
    for item in conditions.get("items_have", []):
        if not state.has_item(item):
            return False

    for item in conditions.get("items_not_have", []):
        if state.has_item(item):
            return False

    return True


def _check_variable_conditions(conditions: Dict[str, Any], state: GameState) -> bool:
    """
    Check variable-related conditions.

    Args:
        conditions: Dictionary containing vars_min, vars_max, and vars_eq keys.
        state: Current game state.

    Returns:
        True if all variable conditions are met, False otherwise.
    """
    for name, min_val in conditions.get("vars_min", {}).items():
        if state.get_var(name) < int(min_val):
            return False

    for name, max_val in conditions.get("vars_max", {}).items():
        if state.get_var(name) > int(max_val):
            return False

    for name, eq_val in conditions.get("vars_eq", {}).items():
        if state.get_var(name) != int(eq_val):
            return False

    return True


def _check_relationship_conditions(conditions: Dict[str, Any], state: GameState) -> bool:
    """
    Check relationship-related conditions.

    Args:
        conditions: Dictionary containing relationships_min key.
        state: Current game state.

    Returns:
        True if all relationship conditions are met, False otherwise.
    """
    for name, min_val in conditions.get("relationships_min", {}).items():
        if state.get_relationship(name) < int(min_val):
            return False

    return True


def _check_flag_conditions(conditions: Dict[str, Any], state: GameState) -> bool:
    """
    Check flag-related conditions.

    Args:
        conditions: Dictionary containing flags_set and flags_not_set keys.
        state: Current game state.

    Returns:
        True if all flag conditions are met, False otherwise.
    """
    for flag in conditions.get("flags_set", []):
        if not state.is_flag(flag):
            return False

    for flag in conditions.get("flags_not_set", []):
        if state.is_flag(flag):
            return False

    return True


def _check_visited_node_conditions(conditions: Dict[str, Any], state: GameState) -> bool:
    """
    Check visited node-related conditions.

    Args:
        conditions: Dictionary containing visited_nodes_include and visited_nodes_exclude keys.
        state: Current game state.

    Returns:
        True if all visited node conditions are met, False otherwise.
    """
    for node_id in conditions.get("visited_nodes_include", []):
        if node_id not in state.visited_nodes:
            return False

    for node_id in conditions.get("visited_nodes_exclude", []):
        if node_id in state.visited_nodes:
            return False

    return True


def check_conditions(conditions: Optional[Dict[str, Any]], state: GameState) -> bool:
    """
    Evaluate structured conditions against game state.

    Supported condition keys:
      - items_have: [str] - Player must have all items
      - items_not_have: [str] - Player must not have any items
      - vars_min: {name: min_value} - Variables must be >= min_value
      - vars_max: {name: max_value} - Variables must be <= max_value
      - vars_eq: {name: exact_value} - Variables must equal exact_value
      - relationships_min: {name: min_value} - Relationships must be >= min_value
      - flags_set: [flag_name] - Flags must be True
      - flags_not_set: [flag_name] - Flags must be False or absent
      - visited_nodes_include: [node_id] - Nodes must be in visited history
      - visited_nodes_exclude: [node_id] - Nodes must not be in visited history

    Args:
        conditions: Dictionary of conditions to evaluate, or None.
        state: Current game state.

    Returns:
        True if all conditions are met or conditions is None, False otherwise.
    """
    if not conditions:
        return True

    return (
        _check_item_conditions(conditions, state)
        and _check_variable_conditions(conditions, state)
        and _check_relationship_conditions(conditions, state)
        and _check_flag_conditions(conditions, state)
        and _check_visited_node_conditions(conditions, state)
    )


def _apply_item_effects(effects: Dict[str, Any], state: GameState) -> None:
    """Apply item-related effects to game state."""
    for item in effects.get("add_items", []):
        state.add_item(item)

    for item in effects.get("remove_items", []):
        state.remove_item(item)


def _apply_variable_effects(effects: Dict[str, Any], state: GameState) -> None:
    """Apply variable-related effects to game state."""
    for name, delta in effects.get("vars_delta", {}).items():
        state.adjust_var(name, int(delta))

    for name, value in effects.get("vars_set", {}).items():
        state.set_var(name, int(value))


def _apply_relationship_effects(effects: Dict[str, Any], state: GameState) -> None:
    """Apply relationship-related effects to game state."""
    for name, delta in effects.get("relationships_delta", {}).items():
        state.adjust_relationship(name, int(delta))


def _apply_flag_effects(effects: Dict[str, Any], state: GameState) -> None:
    """Apply flag-related effects to game state."""
    for name, value in effects.get("set_flags", {}).items():
        state.set_flag(name, bool(value))


def apply_effects(effects: Optional[Dict[str, Any]], state: GameState) -> None:
    """
    Apply effects to game state.

    Supported effect keys:
      - add_items: [str] - Add items to inventory
      - remove_items: [str] - Remove items from inventory
      - vars_delta: {name: delta} - Adjust variables by delta
      - vars_set: {name: value} - Set variables to exact value
      - relationships_delta: {name: delta} - Adjust relationships by delta
      - set_flags: {flag_name: bool} - Set flags to boolean value

    Args:
        effects: Dictionary of effects to apply, or None.
        state: Game state to modify.
    """
    if not effects:
        return

    _apply_item_effects(effects, state)
    _apply_variable_effects(effects, state)
    _apply_relationship_effects(effects, state)
    _apply_flag_effects(effects, state)


class Choice:
    """
    Represents a decision the player can take at a node.
    """

    def __init__(
        self,
        text: str,
        target: str,
        conditions: Optional[Dict[str, Any]] = None,
        effects: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a choice.

        Args:
            text: Display text for the choice.
            target: Node ID to transition to if chosen.
            conditions: Optional conditions that must be met for choice availability.
            effects: Optional effects to apply when choice is selected.
        """
        self.text = text
        self.target = target
        self.conditions = conditions or {}
        self.effects = effects or {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Choice":
        """
        Create a Choice from a dictionary.

        Args:
            data: Dictionary with keys: text, target, conditions (optional), effects (optional).

        Returns:
            A new Choice instance.
        """
        return cls(
            text=data["text"],
            target=data["target"],
            conditions=data.get("conditions"),
            effects=data.get("effects"),
        )

    def is_available(self, state: GameState) -> bool:
        """
        Check if this choice is available given the current game state.

        Args:
            state: Current game state.

        Returns:
            True if all conditions are met, False otherwise.
        """
        return check_conditions(self.conditions, state)

    def apply_effects(self, state: GameState) -> None:
        """
        Apply this choice's effects to the game state.

        Args:
            state: Game state to modify.
        """
        apply_effects(self.effects, state)


class StoryNode:
    """
    A narrative segment containing text and a list of choices.
    """

    def __init__(self, node_id: str, text: str, choices: List[Choice]):
        """
        Initialize a story node.

        Args:
            node_id: Unique identifier for this node.
            text: Narrative text to display.
            choices: List of available choices at this node.
        """
        self.node_id = node_id
        self.text = text
        self.choices = choices

    @classmethod
    def from_dict(cls, node_id: str, data: Dict[str, Any]) -> "StoryNode":
        """
        Create a StoryNode from a dictionary.

        Args:
            node_id: Unique identifier for this node.
            data: Dictionary with keys: text, choices (optional).

        Returns:
            A new StoryNode instance.
        """
        choices = [Choice.from_dict(c) for c in data.get("choices", [])]
        return cls(node_id=node_id, text=data.get("text", ""), choices=choices)

    def available_choices(self, state: GameState) -> List[Choice]:
        """
        Get all choices available in the current game state.

        Args:
            state: Current game state.

        Returns:
            List of available choices.
        """
        return [c for c in self.choices if c.is_available(state)]


class StoryEngine:
    """
    Drives the story by managing state and advancing between nodes.
    """

    def __init__(self, story_data: Dict[str, Any]):
        """
        Initialize the story engine with story data.

        Args:
            story_data: Dictionary containing 'start' node ID and 'nodes' dictionary.

        Raises:
            ValueError: If no valid start node is found.
        """
        self.story_data = story_data
        self.start_node_id: str = self.story_data.get("start", "")
        self.nodes: Dict[str, StoryNode] = {}

        # Load all nodes from story data
        for node_id, node_data in self.story_data.get("nodes", {}).items():
            self.nodes[node_id] = StoryNode.from_dict(node_id, node_data)

        # Validate and set start node
        if not self.start_node_id or self.start_node_id not in self.nodes:
            # Use the first node as start fallback
            self.start_node_id = next(iter(self.nodes.keys()), "")
            if not self.start_node_id:
                logger.warning("No valid start node found in story data")

        self.state = GameState()
        self.current_node_id: str = self.start_node_id
        self.reset()

    def reset(self) -> None:
        """Reset the engine to the initial state."""
        self.state = GameState()
        self.current_node_id = self.start_node_id
        # Mark first node as visited
        self.state.mark_visited(self.current_node_id)

    def get_current_node(self) -> StoryNode:
        """
        Get the current story node.

        Returns:
            The current StoryNode.

        Raises:
            KeyError: If current node ID is not in nodes dictionary.
        """
        return self.nodes[self.current_node_id]

    def get_available_choices(self) -> List[Choice]:
        """
        Get all available choices at the current