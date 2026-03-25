import logging
import random
from typing import Optional, Dict, Tuple

import pygame

import constants as C
from entities import Player, Monster
from mapgen import generate_map, MapData
from ui import UI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Game constants
MAP_SEED_MAX = 1_000_000
GAME_OVER_OVERLAY_ALPHA = 160
GAME_OVER_TEXT_COLOR = (255, 255, 255)
GAME_OVER_SUBTEXT_COLOR = (200, 200, 200)
GAME_OVER_TEXT_OFFSET_Y = 30
GAME_OVER_SUBTEXT_OFFSET_Y = 10


class Game:
    """Main game controller managing event loop, rendering, and game state."""

    def __init__(self):
        """Initialize the game, pygame display, and load the first level."""
        self.screen = pygame.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
        pygame.display.set_caption("Tower of the Sorcerer - Inspired Roguelike")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(C.FONT_NAME, C.FONT_SIZE)
        self.ui = UI(self.font)

        # Initialize game state
        self.level = 1
        self.player = Player(x=1, y=1, hp=C.PLAYER_START_HP)
        self.map_data: Optional[MapData] = None
        self.last_monster_info: Optional[Dict[str, int]] = None
        self.message: str = ""
        self.game_over: bool = False

        self._load_level()
        logger.info("Game initialized")

    def _load_level(self) -> None:
        """Generate a new map for the current level and reset player position."""
        seed = random.randint(0, MAP_SEED_MAX)
        self.map_data = generate_map(seed=seed)
        
        # Position player at map start
        self.player.x, self.player.y = self.map_data.start
        self.last_monster_info = None
        self.message = f"Level {self.level} - Find the door!"
        self.game_over = False
        
        logger.info(f"Loaded level {self.level}")

    def run(self) -> None:
        """Main game loop handling events, updates, and rendering."""
        while True:
            self.clock.tick(C.FPS)
            
            for event in pygame.event.get():
                self._handle_event(event)
            
            self.draw()
            pygame.display.flip()

    def _handle_event(self, event: pygame.event.Event) -> None:
        """Process a single pygame event.
        
        Args:
            event: The pygame event to process.
        """
        if event.type == pygame.QUIT:
            raise SystemExit
        
        if event.type == pygame.KEYDOWN:
            self._handle_keydown(event)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Process keyboard input.
        
        Args:
            event: The pygame KEYDOWN event.
        """
        key = event.key
        
        # Global quit keys
        if key in (pygame.K_ESCAPE, pygame.K_q):
            raise SystemExit
        
        # Game over state: only allow restart
        if self.game_over:
            if key == pygame.K_r:
                self._restart_game()
            return
        
        # Normal gameplay input
        self.handle_input(event)

    def _restart_game(self) -> None:
        """Reset game state and reload the first level."""
        self.level = 1
        self.player.hp = C.PLAYER_START_HP
        self._load_level()
        logger.info("Game restarted")

    def handle_input(self, event: pygame.event.Event) -> None:
        """Process player movement input from keyboard.
        
        Args:
            event: The pygame KEYDOWN event containing movement key.
        """
        key = event.key
        dx, dy = self._get_movement_delta(key)
        
        if dx != 0 or dy != 0:
            self.try_move(dx, dy)

    @staticmethod
    def _get_movement_delta(key: int) -> Tuple[int, int]:
        """Convert keyboard key to movement delta.
        
        Args:
            key: The pygame key constant.
            
        Returns:
            Tuple of (dx, dy) movement deltas.
        """
        movement_map = {
            pygame.K_w: (0, -1),
            pygame.K_s: (0, 1),
            pygame.K_a: (-1, 0),
            pygame.K_d: (1, 0),
        }
        return movement_map.get(key, (0, 0))

    def _in_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within the game grid.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            
        Returns:
            True if coordinates are in bounds, False otherwise.
        """
        return 0 <= x < C.GRID_WIDTH and 0 <= y < C.GRID_HEIGHT

    def try_move(self, dx: int, dy: int) -> None:
        """Attempt to move the player by the given delta.
        
        Handles collision detection with walls, doors, monsters, and chests.
        
        Args:
            dx: Change in x coordinate.
            dy: Change in y coordinate.
        """
        if not self.map_data:
            return
        
        target_x = self.player.x + dx
        target_y = self.player.y + dy
        
        if not self._in_bounds(target_x, target_y):
            return
        
        tile = self.map_data.grid[target_y][target_x]
        is_monster = (target_x, target_y) in self.map_data.monsters
        is_chest = (target_x, target_y) in self.map_data.chests

        # Handle wall collision
        if tile == C.TILE_WALL:
            self.message = "A solid wall blocks your path."
            return

        # Handle door (advance to next level)
        if tile == C.TILE_DOOR:
            self.player.move(dx, dy)
            self.next_level()
            return

        # Handle floor tile with potential overlays
        if tile == C.TILE_FLOOR:
            if is_monster:
                self.fight_monster_at(target_x, target_y)
                if self.game_over:
                    return
            
            if is_chest:
                self.open_chest_at(target_x, target_y)
            
            self.player.move(dx, dy)
            
            if not is_monster and not is_chest:
                self.message = ""
            return

        # Unknown tile type
        self.message = "You can't move there."

    def fight_monster_at(self, x: int, y: int) -> None:
        """Engage in combat with a monster at the given coordinates.
        
        The player takes damage equal to the monster's HP and the monster is removed.
        
        Args:
            x: X coordinate of the monster.
            y: Y coordinate of the monster.
        """
        if not self.map_data:
            return
        
        monster: Optional[Monster] = self.map_data.monsters.get((x, y))
        if monster is None:
            self.message = ""
            return
        
        damage = monster.hp
        self.player.hp -= damage
        self.last_monster_info = {"hp": monster.hp, "damage": damage}
        self.message = f"You fought a monster (HP {monster.hp}) and took {damage} damage."
        
        # Remove defeated monster
        del self.map_data.monsters[(x, y)]
        
        # Check if player died
        if self.player.hp <= 0:
            self.player.hp = 0
            self.game_over = True
            self.message = "You died! Press R to restart."
            logger.info(f"Player died on level {self.level}")

    def open_chest_at(self, x: int, y: int) -> None:
        """Open a chest at the given coordinates and restore player health.
        
        Args:
            x: X coordinate of the chest.
            y: Y coordinate of the chest.
        """
        if not self.map_data:
            return
        
        if (x, y) not in self.map_data.chests:
            return
        
        heal = random.randint(C.CHEST_HEAL_MIN, C.CHEST_HEAL_MAX)
        self.player.hp += heal
        self.map_data.chests.remove((x, y))
        self.message = f"You opened a chest and restored {heal} HP."
        logger.info(f"Chest opened: +{heal} HP")

    def next_level(self) -> None:
        """Advance to the next level, preserving player HP."""
        self.level += 1
        self._load_level()

    def draw(self) -> None:
        """Render the current game state to the screen."""
        self.screen.fill(C.COLOR_BG)
        self._draw_grid()
        self._draw_entities()
        self._draw_player()

        # Draw UI overlay
        self.ui.draw(
            self.screen,
            self.player,
            self.level,
            self.last_monster_info,
            self.message,
        )

        if self.game_over:
            self._draw_game_over_overlay()

    def _draw_grid(self) -> None:
        """Draw the base map tiles (walls, floors, doors) and grid lines."""
        if not self.map_data:
            return
        
        # Draw base tiles
        for y in range(C.GRID_HEIGHT):
            row = self.map_data.grid[y]
            for x in range(C.GRID_WIDTH):
                tile = row[x]
                color = self._get_tile_color(tile)
                rect = pygame.Rect(x * C.TILE_SIZE, y * C.TILE_SIZE, C.TILE_SIZE, C.TILE_SIZE)
                pygame.draw.rect(self.screen, color, rect)

        # Draw grid lines
        self._draw_grid_lines()

        # Draw door on top for clarity
        if self.map_data:
            dx, dy = self.map_data.door
            rect = pygame.Rect(dx * C.TILE_SIZE, dy * C.TILE_SIZE, C.TILE_SIZE, C.TILE_SIZE)
            pygame.draw.rect(self.screen, C.COLOR_DOOR, rect)

    @staticmethod
    def _get_tile_color(tile: int) -> Tuple[int, int, int]:
        """Get the color for a tile type.
        
        Args:
            tile: The tile type constant.
            
        Returns:
            RGB color tuple.
        """
        if tile == C.TILE_WALL:
            return C.COLOR_WALL
        elif tile == C.TILE_DOOR:
            return C.COLOR_DOOR
        else:
            return C.COLOR_FLOOR

    def _draw_grid_lines(self) -> None:
        """Draw the grid lines overlay."""
        # Vertical lines
        for x in range(C.GRID_WIDTH + 1):
            px = x * C.TILE_SIZE
            pygame.draw.line(self.screen, C.COLOR_GRID_LINES, (px, 0), (px, C.WINDOW_HEIGHT))
        
        # Horizontal lines
        for y in range(C.GRID_HEIGHT + 1):
            py = y * C.TILE_SIZE
            pygame.draw.line(
                self.screen,
                C.COLOR_GRID_LINES,
                (0, py),
                (C.GRID_WIDTH * C.TILE_SIZE, py)
            )

    def _draw_entities(self) -> None:
        """Draw all entities (chests and monsters) on the map."""
        if not self.map_data:
            return
        
        # Draw chests
        for (cx, cy) in self.map_data.chests:
            self._draw_entity_at(cx, cy, C.COLOR_CHEST)
        
        # Draw monsters
        for (mx, my) in self.map_data.monsters.keys():
            self._draw_entity_at(mx, my, C.COLOR_MONSTER)

    @staticmethod
    def _draw_entity_at(x: int, y: int, color: Tuple[int, int, int]) -> None:
        """Draw a single entity at the given coordinates.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            color: RGB color tuple.
        """
        rect = pygame.Rect(x * C.TILE_SIZE, y * C.TILE_SIZE, C.TILE_SIZE, C.TILE_SIZE)
        pygame.draw.rect(pygame.display.get_surface(), color, rect)

    def _draw_player(self) -> None:
        """Draw the player character on the map."""
        rect = pygame.Rect(
            self.player.x * C.TILE_SIZE,
            self.player.y * C.TILE_SIZE,
            C.TILE_SIZE,
            C.TILE_SIZE
        )
        pygame.draw.rect(self.screen, C.COLOR_PLAYER, rect)

    def _draw_game_over_overlay(self) -> None:
        """Draw the game over screen overlay with restart instructions."""
        # Semi-transparent overlay
        overlay = pygame.Surface(
            (C.GRID_WIDTH * C.TILE_SIZE, C.WINDOW_HEIGHT),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, GAME_OVER_OVERLAY_ALPHA))
        self.screen.blit(overlay, (0, 0))
        
        # Render text
        text_game_over = self.font.render("Game Over", True, GAME_OVER_TEXT_COLOR)
        text_restart = self.font.render("Press R to restart", True, GAME_OVER_SUBTEXT_COLOR)
        
        # Center text on screen
        center_x = (C.GRID_WIDTH * C.TILE_SIZE) // 2
        center_y = C.WINDOW_HEIGHT // 2
        
        self.screen.blit(
            text_game_over,
            (center_x - text_game_over.get_width() // 2, center_y - GAME_OVER_TEXT_OFFSET_Y)
        )
        self.screen.blit(
            text_restart,
            (center_x - text_restart.get_width() // 2, center_y + GAME_OVER_SUBTEXT_OFFSET_Y)
        )