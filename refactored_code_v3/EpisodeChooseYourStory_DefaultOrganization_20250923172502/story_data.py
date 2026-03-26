import logging
from typing import Any, Dict, List, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_START_NODE = "intro"
RELATIONSHIP_THRESHOLD_FRIENDLY = 2
RELATIONSHIP_PENALTY_RUDE = -2
RELATIONSHIP_BONUS_FRIENDLY = 2
RELATIONSHIP_BONUS_PRAISE = 1
RELATIONSHIP_PENALTY_BETRAY = -3
BRAVERY_INCREMENT = 1
WATCHLIST_FLAG = "watchlisted"
OLD_KEY_ITEM = "Old Key"
ANCIENT_ARTIFACT_ITEM = "Ancient Artifact"


class StoryNode:
    """Represents a single node in the interactive story."""

    def __init__(self, node_id: str, text: str, choices: List[Dict[str, Any]]) -> None:
        """
        Initialize a story node.

        Args:
            node_id: Unique identifier for this node
            text: Narrative text displayed to the player
            choices: List of available choices at this node
        """
        self.node_id = node_id
        self.text = text
        self.choices = choices

    def get_text(self) -> str:
        """
        Retrieve the narrative text for this node.

        Returns:
            The narrative text string
        """
        return self.text

    def get_choices(self) -> List[Dict[str, Any]]:
        """
        Retrieve available choices at this node.

        Returns:
            List of choice dictionaries
        """
        return self.choices

    def is_ending_node(self) -> bool:
        """
        Check if this node is an ending (has no choices).

        Returns:
            True if node has no choices, False otherwise
        """
        return len(self.choices) == 0


class StoryManager:
    """Manages the interactive story state and progression."""

    def __init__(self, story_data: Dict[str, Any]) -> None:
        """
        Initialize the story manager with story data.

        Args:
            story_data: Dictionary containing story structure with 'start' and 'nodes' keys
        """
        self.story_data = story_data
        self.nodes = self._build_nodes()
        self.current_node_id = story_data.get("start", DEFAULT_START_NODE)

    def _build_nodes(self) -> Dict[str, StoryNode]:
        """
        Build StoryNode objects from raw story data.

        Returns:
            Dictionary mapping node IDs to StoryNode objects
        """
        nodes = {}
        for node_id, node_data in self.story_data.get("nodes", {}).items():
            nodes[node_id] = StoryNode(
                node_id=node_id,
                text=node_data.get("text", ""),
                choices=node_data.get("choices", [])
            )
        return nodes

    def get_current_node(self) -> Optional[StoryNode]:
        """
        Retrieve the current story node.

        Returns:
            The current StoryNode or None if node doesn't exist
        """
        return self.nodes.get(self.current_node_id)

    def move_to_node(self, node_id: str) -> bool:
        """
        Move to a specified node.

        Args:
            node_id: ID of the target node

        Returns:
            True if move was successful, False if node doesn't exist
        """
        if node_id not in self.nodes:
            logger.warning(f"Attempted to move to non-existent node: {node_id}")
            return False
        self.current_node_id = node_id
        logger.info(f"Moved to node: {node_id}")
        return True

    def is_at_ending(self) -> bool:
        """
        Check if the current node is an ending node.

        Returns:
            True if at an ending node, False otherwise
        """
        current_node = self.get_current_node()
        return current_node is not None and current_node.is_ending_node()


class PlayerState:
    """Manages player variables, items, relationships, and flags."""

    def __init__(self) -> None:
        """Initialize player state with empty collections."""
        self.variables: Dict[str, int] = {}
        self.items: Set[str] = set()
        self.relationships: Dict[str, int] = {}
        self.flags: Set[str] = set()

    def add_variable(self, var_name: str, delta: int) -> None:
        """
        Modify a player variable by a delta value.

        Args:
            var_name: Name of the variable
            delta: Amount to add (can be negative)
        """
        self.variables[var_name] = self.variables.get(var_name, 0) + delta
        logger.debug(f"Variable '{var_name}' changed by {delta}, now: {self.variables[var_name]}")

    def add_item(self, item_name: str) -> None:
        """
        Add an item to the player's inventory.

        Args:
            item_name: Name of the item to add
        """
        self.items.add(item_name)
        logger.debug(f"Item added: {item_name}")

    def has_item(self, item_name: str) -> bool:
        """
        Check if player has a specific item.

        Args:
            item_name: Name of the item to check

        Returns:
            True if player has the item, False otherwise
        """
        return item_name in self.items

    def modify_relationship(self, character_name: str, delta: int) -> None:
        """
        Modify relationship value with a character.

        Args:
            character_name: Name of the character
            delta: Amount to change relationship by
        """
        self.relationships[character_name] = self.relationships.get(character_name, 0) + delta
        logger.debug(f"Relationship with '{character_name}' changed by {delta}, now: {self.relationships[character_name]}")

    def get_relationship(self, character_name: str) -> int:
        """
        Get current relationship value with a character.

        Args:
            character_name: Name of the character

        Returns:
            Current relationship value (0 if not set)
        """
        return self.relationships.get(character_name, 0)

    def set_flag(self, flag_name: str) -> None:
        """
        Set a boolean flag.

        Args:
            flag_name: Name of the flag to set
        """
        self.flags.add(flag_name)
        logger.debug(f"Flag set: {flag_name}")

    def has_flag(self, flag_name: str) -> bool:
        """
        Check if a flag is set.

        Args:
            flag_name: Name of the flag to check

        Returns:
            True if flag is set, False otherwise
        """
        return flag_name in self.flags

    def apply_effects(self, effects: Dict[str, Any]) -> None:
        """
        Apply all effects from a choice to player state.

        Args:
            effects: Dictionary containing effect types and values
        """
        # Apply variable changes
        for var_name, delta in effects.get("vars_delta", {}).items():
            self.add_variable(var_name, delta)

        # Add items
        for item_name in effects.get("add_items", []):
            self.add_item(item_name)

        # Apply relationship changes
        for character_name, delta in effects.get("relationships_delta", {}).items():
            self.modify_relationship(character_name, delta)

        # Set flags
        for flag_name in effects.get("set_flags", {}).keys():
            self.set_flag(flag_name)


class ConditionChecker:
    """Evaluates conditions to determine if choices are available."""

    def __init__(self, player_state: PlayerState) -> None:
        """
        Initialize condition checker with player state.

        Args:
            player_state: The current player state to check conditions against
        """
        self.player_state = player_state

    def check_items_have(self, required_items: List[str]) -> bool:
        """
        Check if player has all required items.

        Args:
            required_items: List of item names to check

        Returns:
            True if player has all items, False otherwise
        """
        return all(self.player_state.has_item(item) for item in required_items)

    def check_items_not_have(self, forbidden_items: List[str]) -> bool:
        """
        Check if player lacks all specified items.

        Args:
            forbidden_items: List of item names that should not be owned

        Returns:
            True if player has none of the items, False otherwise
        """
        return not any(self.player_state.has_item(item) for item in forbidden_items)

    def check_relationships_min(self, required_relationships: Dict[str, int]) -> bool:
        """
        Check if player meets minimum relationship thresholds.

        Args:
            required_relationships: Dictionary of character names to minimum values

        Returns:
            True if all relationships meet minimum, False otherwise
        """
        return all(
            self.player_state.get_relationship(char) >= min_value
            for char, min_value in required_relationships.items()
        )

    def check_flags_set(self, required_flags: List[str]) -> bool:
        """
        Check if all required flags are set.

        Args:
            required_flags: List of flag names that must be set

        Returns:
            True if all flags are set, False otherwise
        """
        return all(self.player_state.has_flag(flag) for flag in required_flags)

    def check_flags_not_set(self, forbidden_flags: List[str]) -> bool:
        """
        Check if all specified flags are not set.

        Args:
            forbidden_flags: List of flag names that must not be set

        Returns:
            True if none of the flags are set, False otherwise
        """
        return not any(self.player_state.has_flag(flag) for flag in forbidden_flags)

    def check_conditions(self, conditions: Dict[str, Any]) -> bool:
        """
        Evaluate all conditions for a choice.

        Args:
            conditions: Dictionary of condition types and values

        Returns:
            True if all conditions are met, False otherwise
        """
        if not conditions:
            return True

        # Check each condition type
        if "items_have" in conditions:
            if not self.check_items_have(conditions["items_have"]):
                return False

        if "items_not_have" in conditions:
            if not self.check_items_not_have(conditions["items_not_have"]):
                return False

        if "relationships_min" in conditions:
            if not self.check_relationships_min(conditions["relationships_min"]):
                return False

        if "flags_set" in conditions:
            if not self.check_flags_set(conditions["flags_set"]):
                return False

        if "flags_not_set" in conditions:
            if not self.check_flags_not_set(conditions["flags_not_set"]):
                return False

        return True


class InteractiveStory:
    """Main controller for the interactive story experience."""

    def __init__(self, story_data: Dict[str, Any]) -> None:
        """
        Initialize the interactive story.

        Args:
            story_data: Dictionary containing the complete story structure
        """
        self.story_manager = StoryManager(story_data)
        self.player_state = PlayerState()
        self.condition_checker = ConditionChecker(self.player_state)

    def get_current_text(self) -> str:
        """
        Get the narrative text for the current node.

        Returns:
            The current node's narrative text
        """
        current_node = self.story_manager.get_current_node()
        if current_node is None:
            logger.error("Current node is None")
            return "Error: Node not found."
        return current_node.get_text()

    def get_available_choices(self) -> List[Dict[str, Any]]:
        """
        Get all choices available at the current node that meet conditions.

        Returns:
            List of available choice dictionaries
        """
        current_node = self.story_manager.get_current_node()
        if current_node is None:
            return []

        available_choices = []
        for choice in current_node.get_choices():
            conditions = choice.get("conditions", {})
            if self.condition_checker.check_conditions(conditions):
                available_choices.append(choice)

        return available_choices

    def make_choice(self, choice_index: int) -> bool:
        """
        Execute a choice and advance the story.

        Args:
            choice_index: Index of the choice to make

        Returns:
            True if choice was valid and executed, False otherwise
        """
        available_choices = self.get_available_choices()

        if choice_index < 0 or choice_index >= len(available_choices):
            logger.warning(f"Invalid choice index: {choice_index}")
            return False

        choice = available_choices[choice_index]

        # Apply effects
        effects = choice.get("effects", {})
        self.player_state.apply_effects(effects)

        # Move to next node
        target_node = choice.get("target")
        if target_node:
            return self.story_manager.move_to_node(target_node)

        return True

    def is_story_complete(self) -> bool:
        """
        Check if the story has reached an ending.

        Returns:
            True if at an ending node, False otherwise
        """
        return self.story_manager.is_at_ending()


# Story data definition
STORY = {
    "start": "intro",
    "nodes": {
        "intro": {
            "text": (
                "You awaken within the ancient castle of Aster. Rumors speak of a hidden artifact "
                "and a guard who can be friend or foe. Your choices will shape your fate."
            ),
            "choices": [
                {
                    "text": "Explore the courtyard.",
                    "target": "courtyard",
                    "effects": {"vars_delta": {"bravery": BRAVERY_INCREMENT}}
                },
                {
                    "text": "Approach the castle guard.",
                    "target": "guard",
                }
            ]
        },
        "courtyard": {
            "text": (
                "Moonlight paints the courtyard silver. Near the ivy, something gleams beneath fallen leaves."
            ),
            "choices": [
                {
                    "text": "Pick up the old key and head inside.",
                    "target": "hall",
                    "effects": {"add_items": [OLD_KEY_ITEM]}
                },
                {
                    "text": "Ignore it and enter the great hall.",
                    "target": "hall"
                }
            ]
        },
        "guard": {
            "text": (
                "The guard eyes you cautiously. His stance softens as you speak. How do you address him?"
            ),
            "choices": [
                {
                    "text": "Be friendly and respectful.",
                    "target": "hall",
                    "effects": {"relationships_delta": {"Guard": RELATIONSHIP_BONUS_FRIENDLY}}
                },
                {
                    "text": "Be rude and demanding.",
                    "target": "hall",
                    "effects": {
                        "relationships_delta": {"Guard": RELATIONSHIP_PENALTY_RUDE},
                        "set_flags": {WATCHLIST_FLAG: True}
                    }
                }
            ]
        },
        "hall": {
            "text": (
                "The Great Hall bustles with life. Arched doors lead in every direction. The guard watches from afar."
            ),
            "choices": [
                {
                    "text": "Unlock the secret door with the old key.",
                    "target": "secret_passage",
                    "conditions": {"items_have": [OLD_KEY_ITEM]}
                },
                {
                    "text": "Ask the guard to let you into the restricted wing.",
                    "target": "restricted_wing",
                    "conditions": {"relationships_min": {"Guard": RELATIONSHIP_THRESHOLD_FRIENDLY}}
                },
                {
                    "text": "Join the feast and rest a while