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
        Execute tile logic when a player lands on it.

        Args:
            game: The game instance.
            player: The player landing on the tile.

        Returns:
            List[str]: Messages describing what happened.
        """
        return []


class GoTile(Tile):
    """The GO tile at the start of the board."""

    def __init__(self, index: int):
        """Initialize the GO tile."""
        super().__init__(index, "GO")

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle landing on GO (no special action on landing).

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
            # Unowned property available for purchase
            game.pending_purchase_tile = self
            messages.append(f"{player.name} landed on unowned property {self.name}.")
        elif self.owner is player:
            # Player owns the property
            messages.append(f"{player.name} landed on their own property {self.name}.")
        else:
            # Pay rent to owner
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
        amount = self.rent
        player.money -= amount
        self.owner.money += amount
        messages = [f"{player.name} pays ${amount} rent to {self.owner.name} for {self.name}."]
        game.check_bankruptcy(player)
        return messages


class ChanceTile(Tile):
    """Tile that triggers a chance card draw."""

    def __init__(self, index: int):
        """Initialize a chance tile."""
        super().__init__(index, "Chance")

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle landing on a chance tile.

        Args:
            game: The game instance.
            player: The player landing on the tile.

        Returns:
            List[str]: Messages from the chance card drawn.
        """
        messages = [f"{player.name} draws a Chance card..."]
        messages.extend(game.chance_deck.draw(game, player))
        return messages


class FreeParkingTile(Tile):
    """Free Parking tile where players collect accumulated taxes."""

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
            List[str]: Message about collected amount.
        """
        collected = game.free_parking_pot
        game.free_parking_pot = 0
        player.money += collected
        return [f"{player.name} lands on Free Parking and collects ${collected}."]


class JailTile(Tile):
    """Jail tile for just visiting."""

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
            List[str]: Message about visiting jail.
        """
        return [f"{player.name} is just visiting jail."]


class GoToJailTile(Tile):
    """Tile that sends a player to jail."""

    def __init__(self, index: int, jail_index: int):
        """
        Initialize a Go To Jail tile.

        Args:
            index: Position on the board.
            jail_index: Position of the jail tile.
        """
        super().__init__(index, "Go To Jail")
        self.jail_index = jail_index

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle landing on Go To Jail.

        Args:
            game: The game instance.
            player: The player landing on the tile.

        Returns:
            List[str]: Message about being sent to jail.
        """
        game.send_to_jail(player)
        return [f"{player.name} is sent to Jail!"]


class TaxTile(Tile):
    """Tile that charges a tax to the player."""

    def __init__(self, index: int, name: str, amount: int):
        """
        Initialize a tax tile.

        Args:
            index: Position on the board.
            name: Tax name.
            amount: Tax amount to charge.
        """
        super().__init__(index, name)
        self.amount = amount

    def land(self, game: "Game", player: Player) -> List[str]:
        """
        Handle landing on a tax tile.

        Args:
            game: The game instance.
            player: The player landing on the tile.

        Returns:
            List[str]: Message about tax payment.
        """
        player.money -= self.amount
        game.free_parking_pot += self.amount
        game.check_bankruptcy(player)
        return [f"{player.name} pays ${self.amount} in {self.name}. Added to Free Parking pot."]


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
    """Main game controller managing turns, movement, and game state."""

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
        """Get the player whose turn it is."""
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
        Check if a player is bankrupt and handle removal from game.

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

    def _handle_go_passage(self, player: Player, steps: int) -> List[str]:
        """
        Handle GO passage when moving forward.

        Args:
            player: The player moving.
            steps: Number of steps moved.

        Returns:
            List[str]: Messages about GO passage.
        """
        messages = []
        # Award GO salary if passing GO (only for positive forward movement)
        if steps > 0 and (player.position + steps) >= len(self.board.tiles):
            player.money += GO_SALARY
            messages.append(f"{player.name} passed GO and collected ${GO_SALARY}.")
        return messages

    def move_player_steps(self, player: Player, steps: int) -> List[str]:
        """
        Move a player forward by a number of steps.

        Args:
            player: The player to move.
            steps: Number of steps to move.

        Returns:
            List[str]: Messages from movement and tile landing.
        """
        messages = []
        messages.extend(self._handle_go_passage(player, steps))
        player.position = (player.position + steps) % len(self.board.tiles)
        messages.extend(self.process_current_tile(player))
        return messages

    def move_player_to(self, player: Player, target_index: int, award_go_salary: bool = True) -> List[str]:
        """
        Move a player to a specific tile index.

        Args:
            player: The player to move.
            target_index: Target tile index.
            award_go_salary: Whether to award GO salary if moving backwards.

        Returns:
            List[str]: Messages from movement and tile landing.
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

        Guards against deep recursion from chained events.

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

    def attempt_purchase_current