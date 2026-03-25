import logging
from typing import Dict, List, Optional, Any, Set

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_NUMERIC_VALUE = 0
CONDITION_ITEMS_HAVE = "items_have"
CONDITION_ITEMS_NOT_HAVE = "items_not_have"
CONDITION_VARS_MIN = "vars_min"
CONDITION_VARS_MAX = "vars_max"
CONDITION_VARS_EQ = "vars_eq"
CONDITION_RELATIONSHIPS_MIN = "relationships_min"
CONDITION_FLAGS_SET = "flags_set"
CONDITION_FLAGS_NOT_SET = "flags_not_set"
CONDITION_VISITED_INCLUDE = "visited_nodes_include"
CONDITION_VISITED_EXCLUDE = "visited_nodes_exclude"

EFFECT_ADD_ITEMS = "add_items"
EFFECT_REMOVE_ITEMS = "remove_items"
EFFECT_VARS_DELTA = "vars_delta"
EFFECT_VARS_SET = "vars_set"
EFFECT_RELATIONSHIPS_DELTA = "relationships_delta"
EFFECT_SET_FLAGS = "set_flags"

STORY_DATA_START = "start"
STORY_DATA_NODES = "nodes"
CHOICE_TEXT = "text"
CHOICE_TARGET = "target"
CHOICE_CONDITIONS = "conditions"
CHOICE_EFFECTS = "effects"
NODE_TEXT = "text"
NODE_CHOICES = "choices"

SERIALIZATION_ITEMS = "items"
SERIALIZATION_VARIABLES = "variables"
SERIALIZATION_RELATIONSHIPS = "relationships"
SERIALIZATION_FLAGS = "flags"
SERIALIZATION_VISITED = "visited_nodes"
SERIALIZATION_CURRENT_NODE = "current_node_id"
SERIALIZATION_STATE = "state"


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
        current_value = self.variables.get(name, DEFAULT_NUMERIC_VALUE)
        self.variables[name] = current_value + int(delta)

    def set_var(self, name: str, value: int) -> None:
        """Set a variable to a specific value."""
        self.variables[name] = int(value)

    def get_var(self, name: str, default: int = DEFAULT_NUMERIC_VALUE) -> int:
        """Get a variable value with optional default."""
        return self.variables.get(name, default)

    def adjust_relationship(self, name: str, delta: int) -> None:
        """Adjust a relationship value by a delta amount."""
        current_value = self.relationships.get(name, DEFAULT_NUMERIC_VALUE)
        self.relationships[name] = current_value + int(delta)

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
            SERIALIZATION_ITEMS: sorted(list(self.items)),
            SERIALIZATION_VARIABLES: dict(self.variables),
            SERIALIZATION_RELATIONSHIPS: dict(self.relationships),
            SERIALIZATION_FLAGS: dict(self.flags),
            SERIALIZATION_VISITED: list(self.visited_nodes),
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Deserialize game state from a dictionary."""
        self.items = set(data.get(SERIALIZATION_ITEMS, []))
        self.variables = dict(data.get(SERIALIZATION_VARIABLES, {}))
        self.relationships = dict(data.get(SERIALIZATION_RELATIONSHIPS, {}))
        self.flags = dict(data.get(SERIALIZATION_FLAGS, {}))
        self.visited_nodes = list(data.get(SERIALIZATION_VISITED, []))


def _check_items_conditions(conditions: Dict[str, Any], state: GameState) -> bool:
    """Check item-related conditions."""
    for item in conditions.get(CONDITION_ITEMS_HAVE, []):
        if not state.has_item(item):
            return False

    for item in conditions.get(CONDITION_ITEMS_NOT_HAVE, []):
        if state.has_item(item):
            return False

    return True


def _check_variable_conditions(conditions: Dict[str, Any], state: GameState) -> bool:
    """Check variable-related conditions."""
    for name, min_val in conditions.get(CONDITION_VARS_MIN, {}).items():
        if state.get_var(name) < int(min_val):
            return False

    for name, max_val in conditions.get(CONDITION_VARS_MAX, {}).items():
        if state.get_var(name) > int(max_val):
            return False

    for name, eq_val in conditions.get(CONDITION_VARS_EQ, {}).items():
        if state.get_var(name) != int(eq_val):
            return False

    return True


def _check_relationship_conditions(conditions: Dict[str, Any], state: GameState) -> bool:
    """Check relationship-related conditions."""
    for name, min_val in conditions.get(CONDITION_RELATIONSHIPS_MIN, {}).items():
        if state.get_relationship(name) < int(min_val):
            return False

    return True


def _check_flag_conditions(conditions: Dict[str, Any], state: GameState) -> bool:
    """Check flag-related conditions."""
    for flag in conditions.get(CONDITION_FLAGS_SET, []):
        if not state.is_flag(flag):
            return False

    for flag in conditions.get(CONDITION_FLAGS_NOT_SET, []):
        if state.is_flag(flag):
            return False

    return True


def _check_visited_node_conditions(conditions: Dict[str, Any], state: GameState) -> bool:
    """Check visited node-related conditions."""
    for node_id in conditions.get(CONDITION_VISITED_INCLUDE, []):
        if node_id not in state.visited_nodes:
            return False

    for node_id in conditions.get(CONDITION_VISITED_EXCLUDE, []):
        if node_id in state.visited_nodes:
            return False

    return True


def check_conditions(conditions: Optional[Dict[str, Any]], state: GameState) -> bool:
    """
    Evaluate structured conditions against game state.

    Supported condition keys:
      - items_have: [str] - player must have all items
      - items_not_have: [str] - player must not have any items
      - vars_min: {name: min_value} - variables must be >= min_value
      - vars_max: {name: max_value} - variables must be <= max_value
      - vars_eq: {name: exact_value} - variables must equal exact_value
      - relationships_min: {name: min_value} - relationships must be >= min_value
      - flags_set: [flag_name] - flags must be True
      - flags_not_set: [flag_name] - flags must be False or absent
      - visited_nodes_include: [node_id] - all nodes must be visited
      - visited_nodes_exclude: [node_id] - no nodes must be visited

    Args:
        conditions: Dictionary of conditions to check, or None for no conditions
        state: Current game state to evaluate against

    Returns:
        True if all conditions are met, False otherwise
    """
    if not conditions:
        return True

    condition_checks = [
        _check_items_conditions,
        _check_variable_conditions,
        _check_relationship_conditions,
        _check_flag_conditions,
        _check_visited_node_conditions,
    ]

    # All condition checks must pass
    return all(check(conditions, state) for check in condition_checks)


def apply_effects(effects: Optional[Dict[str, Any]], state: GameState) -> None:
    """
    Apply effects to game state.

    Supported effect keys:
      - add_items: [str] - add items to inventory
      - remove_items: [str] - remove items from inventory
      - vars_delta: {name: delta} - adjust variables by delta
      - vars_set: {name: value} - set variables to exact value
      - relationships_delta: {name: delta} - adjust relationships by delta
      - set_flags: {flag_name: bool} - set flags to boolean value

    Args:
        effects: Dictionary of effects to apply, or None for no effects
        state: Game state to modify
    """
    if not effects:
        return

    for item in effects.get(EFFECT_ADD_ITEMS, []):
        state.add_item(item)

    for item in effects.get(EFFECT_REMOVE_ITEMS, []):
        state.remove_item(item)

    for name, delta in effects.get(EFFECT_VARS_DELTA, {}).items():
        state.adjust_var(name, int(delta))

    for name, value in effects.get(EFFECT_VARS_SET, {}).items():
        state.set_var(name, int(value))

    for name, delta in effects.get(EFFECT_RELATIONSHIPS_DELTA, {}).items():
        state.adjust_relationship(name, int(delta))

    for name, value in effects.get(EFFECT_SET_FLAGS, {}).items():
        state.set_flag(name, bool(value))


class Choice:
    """
    Represents a decision the player can take at a story node.
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
            text: Display text for the choice
            target: Node ID to transition to if chosen
            conditions: Optional conditions that must be met for choice availability
            effects: Optional effects to apply when choice is made
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
            data: Dictionary with keys: text, target, conditions (optional), effects (optional)

        Returns:
            Initialized Choice instance
        """
        return cls(
            text=data[CHOICE_TEXT],
            target=data[CHOICE_TARGET],
            conditions=data.get(CHOICE_CONDITIONS),
            effects=data.get(CHOICE_EFFECTS),
        )

    def is_available(self, state: GameState) -> bool:
        """
        Check if this choice is available given the current game state.

        Args:
            state: Current game state

        Returns:
            True if all conditions are met, False otherwise
        """
        return check_conditions(self.conditions, state)

    def apply_effects(self, state: GameState) -> None:
        """
        Apply this choice's effects to the game state.

        Args:
            state: Game state to modify
        """
        apply_effects(self.effects, state)


class StoryNode:
    """
    A narrative segment containing text and a list of available choices.
    """

    def __init__(self, node_id: str, text: str, choices: List[Choice]):
        """
        Initialize a story node.

        Args:
            node_id: Unique identifier for this node
            text: Narrative text to display
            choices: List of available choices at this node
        """
        self.node_id = node_id
        self.text = text
        self.choices = choices

    @classmethod
    def from_dict(cls, node_id: str, data: Dict[str, Any]) -> "StoryNode":
        """
        Create a StoryNode from a dictionary.

        Args:
            node_id: Unique identifier for this node
            data: Dictionary with keys: text, choices (optional)

        Returns:
            Initialized StoryNode instance
        """
        choices = [Choice.from_dict(c) for c in data.get(NODE_CHOICES, [])]
        return cls(node_id=node_id, text=data.get(NODE_TEXT, ""), choices=choices)

    def available_choices(self, state: GameState) -> List[Choice]:
        """
        Get all choices available in the current game state.

        Args:
            state: Current game state

        Returns:
            List of available choices
        """
        return [c for c in self.choices if c.is_available(state)]


class StoryEngine:
    """
    Drives the story by managing game state and advancing between narrative nodes.
    """

    def __init__(self, story_data: Dict[str, Any]):
        """
        Initialize the story engine with story data.

        Args:
            story_data: Dictionary containing story structure with keys:
                       start (optional): starting node ID
                       nodes: dictionary of node_id -> node_data
        """
        self.story_data = story_data
        self.start_node_id: str = self.story_data.get(STORY_DATA_START, "")
        self.nodes: Dict[str, StoryNode] = {}

        # Load all nodes from story data
        for node_id, node_data in self.story_data.get(STORY_DATA_NODES, {}).items():
            self.nodes[node_id] = StoryNode.from_dict(node_id, node_data)

        # Fallback to first node if start node is invalid
        if not self.start_node_id or self.start_node_id not in self.nodes:
            self.start_node_id = next(iter(self.nodes.keys()), "")
            if self.start_node_id:
                logger.warning(
                    "Invalid or missing start node, using first node: %s",
                    self.start_node_id,
                )

        self.state = GameState()
        self.current_node_id: str = self.start_node_id
        self.reset()

    def reset(self) -> None:
        """Reset the engine to initial state."""
        self.state = GameState()
        self.current_node_id = self.start_node_id
        self.state.mark_visited(self.current_node_id)

    def get_current_node(self) -> StoryNode:
        """
        Get the current story node.

        Returns:
            Current StoryNode instance

        Raises:
            KeyError: If current node ID is not in nodes dictionary
        """
        return self.nodes[self.current_node_id]

    def get_available_choices(self) -> List[Choice]:
        """
        Get all available choices at the current node.

        Returns:
            List of available choices based on current game state
        """
        node = self.get_current_node()
        return node.available_choices(self.state)

    def choose(self, choice: Choice)