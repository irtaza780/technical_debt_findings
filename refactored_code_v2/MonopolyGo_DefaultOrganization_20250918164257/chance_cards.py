import logging
import random
from typing import Callable, List

# Configure logging
logger = logging.getLogger(__name__)

# Magic number constants
DIVIDEND_AMOUNT = 100
FINE_AMOUNT = 50
INHERITANCE_AMOUNT = 100
REPAIR_COST_PER_PROPERTY = 25
CHAIRMAN_PAYMENT_PER_PLAYER = 50
MOVE_BACK_SPACES = 3
ADVANCE_SPACES = 5
GO_POSITION = 0
GO_SALARY = 200


class ChanceCard:
    """Encapsulates a single chance card with description and action."""

    def __init__(
        self,
        description: str,
        action: Callable[["Game", "Player"], List[str]],
        is_get_out_of_jail: bool = False,
    ):
        """
        Initialize a ChanceCard.

        Args:
            description: Human-readable card description
            action: Callable that executes the card's effect
            is_get_out_of_jail: Whether this is the special GOOJF card
        """
        self.description = description
        self.action = action
        self.is_get_out_of_jail = is_get_out_of_jail

    def apply(self, game: "Game", player: "Player") -> List[str]:
        """
        Apply this card's action to the player.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings describing the card's effects
        """
        return self.action(game, player)


class ChanceDeck:
    """Manages a shuffled deck of chance cards with special GOOJF handling."""

    def __init__(self):
        """Initialize the chance deck with all cards."""
        self.cards: List[ChanceCard] = []
        self._get_out_card_in_deck: bool = True
        self._build_cards()
        self.shuffle()

    def _build_cards(self) -> None:
        """Build all chance cards and add them to the deck."""
        self.cards.extend(
            [
                ChanceCard("Advance to GO", self._move_to_go),
                ChanceCard(
                    f"Bank pays you dividend of ${DIVIDEND_AMOUNT}",
                    self._bank_pays_dividend,
                ),
                ChanceCard("Go to Jail", self._go_to_jail),
                ChanceCard(f"Pay fine of ${FINE_AMOUNT}", self._pay_fine),
                ChanceCard(f"Inherit ${INHERITANCE_AMOUNT}", self._collect_money),
                ChanceCard(f"Move back {MOVE_BACK_SPACES} spaces", self._move_back_3),
                ChanceCard(f"Advance {ADVANCE_SPACES} spaces", self._advance_5_spaces),
                ChanceCard(
                    f"Property repairs: ${REPAIR_COST_PER_PROPERTY} per property",
                    self._repairs,
                ),
                ChanceCard(
                    f"Chairman of the Board: pay each player ${CHAIRMAN_PAYMENT_PER_PLAYER}",
                    self._chairman,
                ),
                ChanceCard(
                    "Get Out of Jail Free",
                    self._get_out_of_jail,
                    is_get_out_of_jail=True,
                ),
            ]
        )

    def _move_to_go(self, game: "Game", player: "Player") -> List[str]:
        """
        Move player to GO and collect salary.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings
        """
        msgs = [f"Chance: Advance to GO (Collect ${GO_SALARY})."]
        msgs += game.move_player_to(player, GO_POSITION, award_go_salary=True)
        return msgs

    def _bank_pays_dividend(self, game: "Game", player: "Player") -> List[str]:
        """
        Award dividend payment to player.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings
        """
        player.money += DIVIDEND_AMOUNT
        return [f"Chance: Bank pays you dividend of ${DIVIDEND_AMOUNT}."]

    def _go_to_jail(self, game: "Game", player: "Player") -> List[str]:
        """
        Send player directly to jail.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings
        """
        game.send_to_jail(player)
        return [
            "Chance: Go directly to Jail. Do not pass GO, do not collect $200."
        ]

    def _pay_fine(self, game: "Game", player: "Player") -> List[str]:
        """
        Deduct fine from player and add to free parking pot.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings
        """
        player.money -= FINE_AMOUNT
        game.free_parking_pot += FINE_AMOUNT
        game.check_bankruptcy(player)
        return [
            f"Chance: Pay fine of ${FINE_AMOUNT}. Added to Free Parking pot."
        ]

    def _collect_money(self, game: "Game", player: "Player") -> List[str]:
        """
        Award inheritance money to player.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings
        """
        player.money += INHERITANCE_AMOUNT
        return [f"Chance: You inherit ${INHERITANCE_AMOUNT}."]

    def _move_back_3(self, game: "Game", player: "Player") -> List[str]:
        """
        Move player back 3 spaces without GO salary.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings
        """
        new_pos = (player.position - MOVE_BACK_SPACES) % len(game.board.tiles)
        msgs = [f"Chance: Move back {MOVE_BACK_SPACES} spaces."]
        msgs += game.move_player_to(player, new_pos, award_go_salary=False)
        return msgs

    def _advance_5_spaces(self, game: "Game", player: "Player") -> List[str]:
        """
        Move player forward 5 spaces.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings
        """
        msgs = [f"Chance: Advance {ADVANCE_SPACES} spaces."]
        msgs += game.move_player_steps(player, ADVANCE_SPACES)
        return msgs

    def _repairs(self, game: "Game", player: "Player") -> List[str]:
        """
        Charge player for property repairs based on owned properties.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings
        """
        property_count = len(player.properties)
        total_cost = REPAIR_COST_PER_PROPERTY * property_count

        if total_cost > 0:
            player.money -= total_cost
            game.free_parking_pot += total_cost
            game.check_bankruptcy(player)
            return [
                f"Chance: Property repairs. Pay ${REPAIR_COST_PER_PROPERTY} x {property_count} = ${total_cost}. Added to Free Parking pot."
            ]
        else:
            return ["Chance: No properties. No repair costs."]

    def _chairman(self, game: "Game", player: "Player") -> List[str]:
        """
        Charge player to pay all other players as chairman.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings
        """
        total_paid = 0
        # Pay each non-bankrupt opponent
        for other_player in game.players:
            if other_player is not player and not other_player.bankrupt:
                player.money -= CHAIRMAN_PAYMENT_PER_PLAYER
                other_player.money += CHAIRMAN_PAYMENT_PER_PLAYER
                total_paid += CHAIRMAN_PAYMENT_PER_PLAYER

        game.check_bankruptcy(player)
        return [
            f"Chance: Elected Chairman. Pay ${CHAIRMAN_PAYMENT_PER_PLAYER} to each player. Total paid: ${total_paid}."
        ]

    def _get_out_of_jail(self, game: "Game", player: "Player") -> List[str]:
        """
        Award Get Out of Jail Free card to player.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings
        """
        player.get_out_of_jail_cards += 1
        self._get_out_card_in_deck = False
        return [
            "Chance: Get Out of Jail Free card received. Hold until needed."
        ]

    def shuffle(self) -> None:
        """Shuffle the deck of chance cards."""
        random.shuffle(self.cards)

    def draw(self, game: "Game", player: "Player") -> List[str]:
        """
        Draw a card from the deck and apply its effect.

        Handles special logic for the Get Out of Jail Free card, which is
        removed from circulation when held by a player.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            List of message strings describing the card drawn and its effects
        """
        # Attempt to draw a card, cycling through deck if GOOJF is unavailable
        max_attempts = len(self.cards)
        for _ in range(max_attempts):
            card = self.cards.pop(0)

            # If GOOJF is held by a player, defer it and try next card
            if card.is_get_out_of_jail and not self._get_out_card_in_deck:
                self.cards.append(card)
                continue

            # Apply the card
            messages = [f"Card: {card.description}"]
            messages += card.apply(game, player)

            # Return card to bottom of deck
            self.cards.append(card)
            return messages

        # Fallback (should not occur in normal gameplay)
        logger.warning("No available Chance card could be drawn after max attempts")
        return ["No available Chance card could be drawn."]

    def return_get_out_of_jail_card(self) -> None:
        """
        Mark the Get Out of Jail Free card as available for drawing again.

        Called when a player uses their GOOJF card.
        """
        self._get_out_card_in_deck = True