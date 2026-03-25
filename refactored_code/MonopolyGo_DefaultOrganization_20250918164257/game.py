import logging
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

from chance_cards import ChanceDeck

# Game Constants
START_MONEY = 1500
GO_SALARY = 200
JAIL_FINE = 50
MAX_DOUBLES_ALLOWED = 3
MAX_JAIL_ATTEMPTS = 3
BOARD_SIZE = 20
JAIL_INDEX = 5
EVENT_CHAIN_LIMIT = 12

# Configure logging
logger = logging.getLogger(__name__)


class Dice:
    """Handles dice rolling for the game."""

    def roll(self) -> Tuple[int, int]:
        """
        Roll two six-sided dice.

        Returns:
            Tuple[int, int]: Two random integers between 1 and 6.
        """
        return random.randint(1, 6), random.randint(1, 6)


@dataclass
class Player:
    """Represents a player in the game."""

    name: str
    color: str = "red"
    money: int = START_MONEY
    position: int = 0
    in_jail: bool = False
    jail_turns: int = 0
    get_out_of_jail_cards: int = 0
    properties: List[int] = field(default_factory=list)
    consecutive_doubles: int = 0
    bankrupt: bool = False


class Tile:
    """Base class for all board tiles."""

    def __init__(self, index: int, name: str):
        """
        Initialize a tile.

        Args:
            index: Position on the board.
            name: Display name of the tile.
        """
        self.index = index
        self.name = name

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle a player landing on this tile.

        Args:
            game: The game instance.
            player: The player landing on the tile.

        Returns:
            List[str]: Messages describing what happened.
        """
        return []


class GoTile(Tile):
    """The GO tile where players start."""

    def __init__(self, index: int):
        """Initialize the GO tile."""
        super().__init__(index, "GO")

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle landing on GO.

        Args:
            game: The game instance.
            player: The player landing on GO.

        Returns:
            List[str]: Landing message.
        """
        return [f"{player.name} landed on GO."]


class PropertyTile(Tile):
    """Represents a purchasable property on the board."""

    def __init__(self, index: int, name: str, price: int, rent: int, color_group: str):
        """
        Initialize a property tile.

        Args:
            index: Position on the board.
            name: Property name.
            price: Purchase price.
            rent: Rent amount when owned.
            color_group: Color group for property sets.
        """
        super().__init__(index, name)
        self.price = price
        self.rent = rent
        self.color_group = color_group
        self.owner: Optional[Player] = None

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle landing on a property.

        Args:
            game: The game instance.
            player: The player landing on the property.

        Returns:
            List[str]: Messages describing the outcome.
        """
        messages = []

        if self.owner is None:
            game.pending_purchase_tile = self
            messages.append(f"{player.name} landed on unowned property {self.name}.")
        elif self.owner is player:
            messages.append(f"{player.name} landed on their own property {self.name}.")
        else:
            messages.extend(self._collect_rent(game, player))

        return messages

    def _collect_rent(self, game: "Game", player: Player) -> List[str]:
        """
        Collect rent from a player landing on owned property.

        Args:
            game: The game instance.
            player: The player owing rent.

        Returns:
            List[str]: Messages describing the rent transaction.
        """
        player.money -= self.rent
        self.owner.money += self.rent
        messages = [
            f"{player.name} pays ${self.rent} rent to {self.owner.name} for {self.name}."
        ]
        game.check_bankruptcy(player)
        return messages


class ChanceTile(Tile):
    """Represents a Chance card tile."""

    def __init__(self, index: int):
        """Initialize a Chance tile."""
        super().__init__(index, "Chance")

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle landing on Chance.

        Args:
            game: The game instance.
            player: The player landing on Chance.

        Returns:
            List[str]: Messages from the Chance card drawn.
        """
        messages = [f"{player.name} draws a Chance card..."]
        messages.extend(game.chance_deck.draw(game, player))
        return messages


class FreeParkingTile(Tile):
    """Represents the Free Parking tile."""

    def __init__(self, index: int):
        """Initialize the Free Parking tile."""
        super().__init__(index, "Free Parking")

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle landing on Free Parking.

        Args:
            game: The game instance.
            player: The player landing on Free Parking.

        Returns:
            List[str]: Messages describing the collection.
        """
        collected = game.free_parking_pot
        game.free_parking_pot = 0
        player.money += collected
        return [f"{player.name} lands on Free Parking and collects ${collected}."]


class JailTile(Tile):
    """Represents the Jail tile (just visiting)."""

    def __init__(self, index: int):
        """Initialize the Jail tile."""
        super().__init__(index, "Jail / Just Visiting")

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle landing on Jail (just visiting).

        Args:
            game: The game instance.
            player: The player landing on Jail.

        Returns:
            List[str]: Landing message.
        """
        return [f"{player.name} is just visiting jail."]


class GoToJailTile(Tile):
    """Represents the Go To Jail tile."""

    def __init__(self, index: int, jail_index: int):
        """
        Initialize the Go To Jail tile.

        Args:
            index: Position on the board.
            jail_index: Position of the Jail tile.
        """
        super().__init__(index, "Go To Jail")
        self.jail_index = jail_index

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle landing on Go To Jail.

        Args:
            game: The game instance.
            player: The player landing on Go To Jail.

        Returns:
            List[str]: Messages about being sent to jail.
        """
        game.send_to_jail(player)
        return [f"{player.name} is sent to Jail!"]


class TaxTile(Tile):
    """Represents a tax tile."""

    def __init__(self, index: int, name: str, amount: int):
        """
        Initialize a tax tile.

        Args:
            index: Position on the board.
            name: Tax name.
            amount: Tax amount.
        """
        super().__init__(index, name)
        self.amount = amount

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle landing on a tax tile.

        Args:
            game: The game instance.
            player: The player landing on the tax tile.

        Returns:
            List[str]: Messages describing the tax payment.
        """
        player.money -= self.amount
        game.free_parking_pot += self.amount
        game.check_bankruptcy(player)
        return [
            f"{player.name} pays ${self.amount} in {self.name}. Added to Free Parking pot."
        ]


class Board:
    """Represents the game board with all tiles."""

    def __init__(self):
        """Initialize the board with 20 tiles."""
        self.tiles: List[Tile] = []
        self.jail_index = JAIL_INDEX
        self._build()

    def _build(self):
        """Build the board with all tiles in order."""
        # 0: GO
        self.tiles.append(GoTile(0))
        # 1: Property
        self.tiles.append(PropertyTile(1, "Old Kent Road", 60, 2, "Brown"))
        # 2: Chance
        self.tiles.append(ChanceTile(2))
        # 3: Property
        self.tiles.append(PropertyTile(3, "Whitechapel Road", 60, 4, "Brown"))
        # 4: Tax
        self.tiles.append(TaxTile(4, "Income Tax", 100))
        # 5: Jail
        self.tiles.append(JailTile(5))
        # 6: Property
        self.tiles.append(PropertyTile(6, "The Angel Islington", 100, 6, "Light Blue"))
        # 7: Free Parking
        self.tiles.append(FreeParkingTile(7))
        # 8: Property
        self.tiles.append(PropertyTile(8, "Euston Road", 100, 6, "Light Blue"))
        # 9: Chance
        self.tiles.append(ChanceTile(9))
        # 10: Property
        self.tiles.append(PropertyTile(10, "Pentonville Road", 140, 10, "Pink"))
        # 11: Go To Jail
        self.tiles.append(GoToJailTile(11, self.jail_index))
        # 12: Property
        self.tiles.append(PropertyTile(12, "Pall Mall", 140, 10, "Pink"))
        # 13: Chance
        self.tiles.append(ChanceTile(13))
        # 14: Property
        self.tiles.append(PropertyTile(14, "Whitehall", 160, 12, "Orange"))
        # 15: Property
        self.tiles.append(PropertyTile(15, "Fleet Street", 160, 12, "Orange"))
        # 16: Chance
        self.tiles.append(ChanceTile(16))
        # 17: Property
        self.tiles.append(PropertyTile(17, "Trafalgar Square", 180, 14, "Red"))
        # 18: Tax
        self.tiles.append(TaxTile(18, "Luxury Tax", 100))
        # 19: Chance
        self.tiles.append(ChanceTile(19))


class Game:
    """Manages the overall game state and turn logic."""

    def __init__(self, players: List[Player]):
        """
        Initialize a new game.

        Args:
            players: List of players participating in the game.
        """
        self.players: List[Player] = players
        self.board = Board()
        self.dice = Dice()
        self.chance_deck = ChanceDeck()
        self.current_player_index: int = 0
        self.free_parking_pot: int = 0
        self.log: List[str] = []
        self.last_roll: Optional[Tuple[int, int]] = None
        self.pending_purchase_tile: Optional[PropertyTile] = None
        self.roll_again_allowed: bool = False
        self.turn_has_not_rolled: bool = True
        self.waiting_for_roll: Optional[bool] = True
        # Guard against deep event chains (e.g., chained Chance movements)
        self._event_chain_depth: int = 0
        self._event_chain_limit: int = EVENT_CHAIN_LIMIT
        # Game-over state
        self.game_over: bool = False

    @property
    def current_player(self) -> Player:
        """Get the current active player."""
        return self.players[self.current_player_index]

    def log_message(self, msg: str):
        """
        Add a message to the game log.

        Args:
            msg: Message to log.
        """
        self.log.append(msg)
        logger.info(msg)

    def check_bankruptcy(self, player: Player):
        """
        Check if a player is bankrupt and handle accordingly.

        Args:
            player: The player to check.
        """
        if player.money < 0 and not player.bankrupt:
            player.bankrupt = True
            # Release owned properties back to bank
            for idx in list(player.properties):
                tile = self.board.tiles[idx]
                if hasattr(tile, "owner"):
                    tile.owner = None
            player.properties.clear()
            self.log_message(
                f"{player.name} is bankrupt and removed from play. "
                "Their properties return to the bank."
            )

    def move_player_steps(self, player: Player, steps: int) -> List[str]:
        """
        Move a player forward by a number of steps.

        Args:
            player: The player to move.
            steps: Number of spaces to move.

        Returns:
            List[str]: Messages from the movement and tile landing.
        """
        messages = []
        new_pos = (player.position + steps) % len(self.board.tiles)

        # Handle passing GO (only for positive forward movement)
        if steps > 0 and (player.position + steps) >= len(self.board.tiles):
            player.money += GO_SALARY
            messages.append(f"{player.name} passed GO and collected ${GO_SALARY}.")

        player.position = new_pos
        messages.extend(self.process_current_tile(player))
        return messages

    def move_player_to(
        self, player: Player, target_index: int, award_go_salary: bool = True
    ) -> List[str]:
        """
        Move a player to a specific tile index.

        Args:
            player: The player to move.
            target_index: Target tile index.
            award_go_salary: Whether to award GO salary if passing GO.

        Returns:
            List[str]: Messages from the movement and tile landing.
        """
        messages = []
        old_pos = player.position

        # Award GO salary if moving backwards (passing GO)
        if award_go_salary and target_index < old_pos:
            player.money += GO_SALARY
            messages.append(f"{player.name} passed GO and collected ${GO_SALARY}.")

        player.position = target_index
        messages.extend(self.process_current_tile(player))
        return messages

    def process_current_tile(self, player: Player) -> List[str]:
        """
        Process the tile the player is currently on.

        Includes recursion guard to prevent infinite event chains.

        Args:
            player: The player on the tile.

        Returns:
            List[str]: Messages from tile processing.
        """
        # Guard against deep recursion due to chained events
        if self._event_chain_depth >= self._event_chain_limit:
            return ["Event chain limit reached."]

        self._event_chain_depth += 1
        try:
            tile = self.board.tiles[player.position]
            messages = tile.land(self, player)
            return messages
        finally:
            self._event_chain_depth -= 1

    def attempt_purchase_current_tile(self) -> str:
        """
        Attempt to purchase the pending property tile.

        Returns:
            str: Message describing the outcome.
        """
        tile = self.pending_purchase_tile
        player = self.current_player

        if tile is None or tile.owner is not None:
            return "No property available for purchase."

        if player.money < tile.price:
            return f"{player.name} cannot afford {tile.name} (${tile.price})."

        tile.owner = player