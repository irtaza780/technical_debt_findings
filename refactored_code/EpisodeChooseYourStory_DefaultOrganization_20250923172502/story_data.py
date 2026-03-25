import logging
from typing import Any, Dict, List, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_START_NODE = "intro"
RELATIONSHIP_THRESHOLD_HIGH = 2
RELATIONSHIP_THRESHOLD_LOW = -2
BRAVERY_INCREMENT = 1
GUARD_RELATIONSHIP_FRIENDLY = 2
GUARD_RELATIONSHIP_HOSTILE = -2
GUARD_RELATIONSHIP_BETRAYAL = -3
GUARD_RELATIONSHIP_GRATITUDE = 1
OLD_KEY_ITEM = "Old Key"
ANCIENT_ARTIFACT_ITEM = "Ancient Artifact"
WATCHLIST_FLAG = "watchlisted"

# Story structure
STORY = {
    "start": DEFAULT_START_NODE,
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
                    "effects": {"relationships_delta": {"Guard": GUARD_RELATIONSHIP_FRIENDLY}}
                },
                {
                    "text": "Be rude and demanding.",
                    "target": "hall",
                    "effects": {
                        "relationships_delta": {"Guard": GUARD_RELATIONSHIP_HOSTILE},
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
                    "conditions": {"relationships_min": {"Guard": RELATIONSHIP_THRESHOLD_HIGH}}
                },
                {
                    "text": "Join the feast and rest a while.",
                    "target": "feast"
                },
                {
                    "text": "Sneak toward the treasury.",
                    "target": "sneak_attempt"
                }
            ]
        },
        "sneak_attempt": {
            "text": (
                "You move in the shadows, steps measured and breath held. A shout could end it all..."
            ),
            "choices": [
                {
                    "text": "Continue.",
                    "target": "jail",
                    "conditions": {"flags_set": [WATCHLIST_FLAG]},
                    "effects": {"vars_delta": {"bravery": BRAVERY_INCREMENT}}
                },
                {
                    "text": "Continue.",
                    "target": "treasury",
                    "conditions": {"flags_not_set": [WATCHLIST_FLAG]},
                    "effects": {"vars_delta": {"bravery": BRAVERY_INCREMENT}}
                }
            ]
        },
        "jail": {
            "text": (
                "A whistle pierces the night. Rough hands seize you. The cell door slams—the castle remembers its enemies."
            ),
            "choices": []
        },
        "treasury": {
            "text": (
                "Vaulted ceilings arch above rows of gilded chests. A pedestal bears an ancient artifact pulsing faintly."
            ),
            "choices": [
                {
                    "text": "Take the artifact and leave quietly.",
                    "target": "escape",
                    "effects": {
                        "add_items": [ANCIENT_ARTIFACT_ITEM],
                        "vars_delta": {"bravery": BRAVERY_INCREMENT}
                    }
                },
                {
                    "text": "Leave it untouched and slip away.",
                    "target": "escape"
                }
            ]
        },
        "secret_passage": {
            "text": (
                "Behind the door, a narrow stair spirals down. Cool air whispers secrets from the depths."
            ),
            "choices": [
                {
                    "text": "Descend into the darkness.",
                    "target": "underground_lake",
                    "effects": {"vars_delta": {"bravery": BRAVERY_INCREMENT}}
                },
                {
                    "text": "Return to the Great Hall.",
                    "target": "hall"
                }
            ]
        },
        "underground_lake": {
            "text": (
                "An underground lake glows with blue light. A small boat waits, tethered to a weathered post."
            ),
            "choices": [
                {
                    "text": "Sail across the lake.",
                    "target": "ending_mystic",
                    "conditions": {"items_have": [ANCIENT_ARTIFACT_ITEM]}
                },
                {
                    "text": "Sail across the lake.",
                    "target": "ending_lost",
                    "conditions": {"items_not_have": [ANCIENT_ARTIFACT_ITEM]}
                }
            ]
        },
        "restricted_wing": {
            "text": (
                "With a nod, the guard escorts you past the velvet rope. Corridors twist toward the old tower."
            ),
            "choices": [
                {
                    "text": "Ask for help accessing the tower.",
                    "target": "tower",
                    "effects": {"relationships_delta": {"Guard": GUARD_RELATIONSHIP_GRATITUDE}}
                },
                {
                    "text": "Betray the guard and sprint toward the treasury.",
                    "target": "sneak_attempt",
                    "effects": {
                        "relationships_delta": {"Guard": GUARD_RELATIONSHIP_BETRAYAL},
                        "set_flags": {WATCHLIST_FLAG: True}
                    }
                }
            ]
        },
        "feast": {
            "text": (
                "Laughter rises with the music. Plates overflow, and cares drift away in the warm candlelight."
            ),
            "choices": [
                {
                    "text": "Eat and rest the night away.",
                    "target": "ending_peace"
                },
                {
                    "text": "Toast the guard for keeping everyone safe.",
                    "target": "ending_popular",
                    "effects": {"relationships_delta": {"Guard": GUARD_RELATIONSHIP_GRATITUDE}}
                }
            ]
        },
        "tower": {
            "text": (
                "Atop the tower, wind sings across the battlements. A dust-covered chest rests against the wall."
            ),
            "choices": [
                {
                    "text": "Open the chest with the old key.",
                    "target": "ending_hero",
                    "conditions": {"items_have": [OLD_KEY_ITEM]}
                },
                {
                    "text": "Gaze across the lands and return downstairs.",
                    "target": "ending_peace"
                }
            ]
        },
        "escape": {
            "text": (
                "You plan your exit. The gate is guarded, the walls are high, and night deepens."
            ),
            "choices": [
                {
                    "text": "Ask the guard to wave you through the gate.",
                    "target": "ending_assisted_escape",
                    "conditions": {"relationships_min": {"Guard": RELATIONSHIP_THRESHOLD_HIGH}}
                },
                {
                    "text": "Make a break for it now.",
                    "target": "ending_caught",
                    "conditions": {"flags_set": [WATCHLIST_FLAG]}
                },
                {
                    "text": "Slip away under moonlight.",
                    "target": "ending_free",
                    "conditions": {"flags_not_set": [WATCHLIST_FLAG]}
                },
                {
                    "text": "Change your mind and return to the Great Hall.",
                    "target": "hall"
                }
            ]
        },
        "ending_mystic": {
            "text": (
                "Artifact in hand, the lake parts as if obeying your will. You vanish into a realm of shimmering dawns—"
                "a legend reborn."
            ),
            "choices": []
        },
        "ending_lost": {
            "text": (
                "The mist thickens. Your boat turns in circles until the lantern gutters out. When light returns, "
                "the castle—and you—are never seen again."
            ),
            "choices": []
        },
        "ending_hero": {
            "text": (
                "Within the chest lies a seal of kingship. You deliver it to the people, and the castle awakens to justice."
            ),
            "choices": []
        },
        "ending_peace": {
            "text": (
                "You choose a gentle path. In quiet days that follow, the castle becomes a second home."
            ),
            "choices": []
        },
        "ending_popular": {
            "text": (
                "Your praise spreads like firelight. The guard becomes your staunch ally, and doors open before you."
            ),
            "choices": []
        },
        "ending_assisted_escape": {
            "text": (
                "With a discreet nod, the guard lifts the bar. You pass into the cool night, owing a friend a favor."
            ),
            "choices": []
        },
        "ending_caught": {
            "text": (
                "Torches flare and a net drops from above. The castle has long memories, and your face is now among them."
            ),
            "choices": []
        },
        "ending_free": {
            "text": (
                "Hand over hand, you crest the wall and disappear into the wilds. Freedom tastes like starlight."
            ),
            "choices": []
        }
    }
}


class GameState:
    """Manages player state including inventory, relationships, variables, and flags."""

    def __init__(self) -> None:
        """Initialize a new game state with empty collections."""
        self.inventory: List[str] = []
        self.relationships: Dict[str, int] = {}
        self.variables: Dict[str, int] = {}
        self.flags: Set[str] = set()

    def add_item(self, item: str) -> None:
        """
        Add an item to the player's inventory.

        Args:
            item: The name of the item to add.
        """
        if item not in self.inventory:
            self.inventory.append(item)
            logger.info(f"Added item: {item}")

    def has_item(self, item: str) -> bool:
        """
        Check if the player has a specific item.

        Args:
            item: The name of the item to check.

        Returns:
            True if the item is in inventory, False otherwise.
        """
        return item in self.inventory

    def has_items(self, items: List[str]) -> bool:
        """
        Check if the player has all items in a list.

        Args:
            items: List of item names to check.

        Returns:
            True if all items are in inventory, False otherwise.
        """
        return all(self.has_item(item) for item in items)

    def lacks_items(self, items: List[str]) -> bool:
        """
        Check if the player lacks all items in a list.

        Args:
            items: List of item names to check.

        Returns:
            True if none of the items are in inventory, False otherwise.
        """
        return not any(self.has_item(item) for item in items)

    def set_relationship(self, character: str, value: int) -> None:
        """
        Set a character relationship to a specific value.

        Args:
            character: The name of the character.
            value: The relationship value to set.
        """
        self.relationships[character] = value
        logger.info(f"Set {character} relationship to {value}")

    def adjust_relationship(self, character: str, delta: int) -> None:
        """
        Adjust a character relationship by a delta value.

        Args:
            character: The name of the character.
            delta: The amount to adjust the relationship by.
        """
        current = self.relationships.get(character, 0)
        self.relationships[character] = current + delta
        logger.info(f"Adjusted {character} relationship by {delta} (now {self.relationships[character]})")

    def get_relationship(self, character: str) -> int:
        """
        Get the current relationship value with a character.

        Args:
            character: The name of the character.

        Returns:
            The relationship value, defaulting to 0 if not set.
        """
        return self.relationships.get(character, 0)

    def meets_relationship_minimum(self, character: str, minimum: int) -> bool:
        """
        Check if a character relationship meets a minimum threshold.

        Args:
            character: The name of the character.
            minimum: The minimum relationship value required.

        Returns:
            True if the relationship meets or exceeds the minimum, False otherwise.
        """
        return self.get_relationship(character) >= minimum

    def set_variable(self, var_name: str, value: int) -> None:
        """
        Set a game variable to a specific value.

        Args:
            var_name: The name of the variable.
            value: The value to set.
        """
        self.variables[var_name] = value
        logger.info(f"Set variable {var_name} to {value}")

    def adjust_variable(self, var_name: str, delta: int) -> None:
        """
        Adjust a game variable by a delta value.

        Args:
            var_name: The name of the variable.
            delta: The amount to adjust the variable by.
        """
        current = self.variables.get(var_name, 0)
        self.variables[var_name] = current + delta
        logger.info(f"Adjusted variable {var_name} by {delta} (now {self.variables[var_name]})")

    def set_flag(self, flag_name: str) -> None:
        """
        Set a boolean flag to True.

        Args:
            flag_name: The name of the flag to set.
        """
        self.flags.add(flag_name)
        logger.info(f"Set flag: {flag_name}")

    def has_flag(self, flag_name: str) -> bool:
        """
        Check if a flag is set.

        Args:
            flag_name: The name of the flag to check.

        Returns:
            True if the flag is set, False otherwise.
        """
        return flag_name in self.flags

    def has_flags(self, flag_names: List[str]) -> bool:
        """
        Check if all flags in a list are set.

        Args:
            flag_names: List of flag names to check.

        Returns:
            True if all flags are set, False otherwise.
        """
        return all(self.has_flag(flag) for flag in flag_names)

    def lacks_flags(self, flag_names: List[str]) -> bool:
        """
        Check if none of the flags