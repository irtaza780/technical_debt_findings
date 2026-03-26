import logging
import random
from typing import Optional, Dict, Tuple

import pygame

import constants as C
from entities import Player, Monster
from mapgen import generate_map, MapData
from ui import UI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Game state constants
RESTART_KEY = pygame.K_r
QUIT_KEYS = (pygame.K_ESCAPE, pygame.K_q)
MOVEMENT_KEYS = {
    pygame.K_w: (0, -1),
    pygame.K_s: (0, 1),
    pygame.K_a: (-1, 0),
    pygame.K_d: (1, 0),
}

# Overlay constants
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

    def _load_level(self) -> None:
        """Generate a new map for the current level and reset player position."""
        seed = random.randint(0, 1_000_000)
        self.map_data = generate_map(seed=seed)
        
        # Position player at map start
        self.player.x, self.player.y = self.map_data.start
        self.last_monster_info = None
        self.message = f"Level {self.level} - Find the door!"
        self.game_over = False
        logger.info(f"Loaded level {self.level}")

    def run(self) -> None:
        """Main game loop: handle events, update state, and render."""
        while True:
            self.clock.tick(C.FPS)
            
            for event in pygame.event.get():
                self._handle_event(event)
            
            self.draw()
            pygame.display.flip()

    def _handle_event(self, event: pygame.event.Event) -> None:
        """Process a single pygame event."""
        if event.type == pygame.QUIT:
            raise SystemExit
        
        if event.type == pygame.KEYDOWN:
            self._handle_keydown(event)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Handle keyboard input based on game state."""
        key = event.key
        
        # Global quit keys
        if key in QUIT_KEYS:
            raise SystemExit
        
        # Game over state: only allow restart
        if self.game_over:
            if key == RESTART_KEY:
                self._restart_game()
            return
        
        # Normal gameplay: handle movement
        if key in MOVEMENT_KEYS:
            dx, dy = MOVEMENT_KEYS[key]
            self.try_move(dx, dy)

    def _restart_game(self) -> None:
        """Reset game to initial state and reload level 1."""
        self.level = 1
        self.player.hp = C.PLAYER_START_HP
        self._load_level()
        logger.info("Game restarted")

    def _in_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within the game grid."""
        return 0 <= x < C.GRID_WIDTH and 0 <= y < C.GRID_HEIGHT

    def try_move(self, dx: int, dy: int) -> None:
        """Attempt to move the player by (dx, dy), handling collisions and interactions."""
        if not self.map_data:
            return
        
        target_x = self.player.x + dx
        target_y = self.player.y + dy
        
        if not self._in_bounds(target_x, target_y):
            return
        
        tile = self.map_data.grid[target_y][target_x]
        
        # Handle wall collision
        if tile == C.TILE_WALL:
            self.message = "A solid wall blocks your path."
            return
        
        # Handle door: advance to next level
        if tile == C.TILE_DOOR:
            self.player.move(dx, dy)
            self.next_level()
            return
        
        # Handle floor tile with possible overlays
        if tile == C.TILE_FLOOR:
            self._handle_floor_interactions(target_x, target_y)
            if not self.game_over:
                self.player.move(dx, dy)
            return
        
        # Unknown tile type
        self.message = "You can't move there."

    def _handle_floor_interactions(self, x: int, y: int) -> None:
        """Handle interactions with entities on a floor tile (monsters, chests)."""
        has_monster = (x, y) in self.map_data.monsters
        has_chest = (x, y) in self.map_data.chests
        
        if has_monster:
            self.fight_monster_at(x, y)
        
        if has_chest and not self.game_over:
            self.open_chest_at(x, y)
        
        # Clear message if no interactions occurred
        if not has_monster and not has_chest:
            self.message = ""

    def fight_monster_at(self, x: int, y: int) -> None:
        """Engage in combat with a monster at the given coordinates."""
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
            self._handle_player_death()

    def _handle_player_death(self) -> None:
        """Handle player death state."""
        self.player.hp = 0
        self.game_over = True
        self.message = "You died! Press R to restart."
        logger.info(f"Player died on level {self.level}")

    def open_chest_at(self, x: int, y: int) -> None:
        """Open a chest at the given coordinates and restore player health."""
        if not self.map_data or (x, y) not in self.map_data.chests:
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
        """Render the entire game state to the screen."""
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
        
        # Draw door on top for visibility
        self._draw_door()

    def _get_tile_color(self, tile: int) -> Tuple[int, int, int]:
        """Return the color for a given tile type."""
        if tile == C.TILE_WALL:
            return C.COLOR_WALL
        elif tile == C.TILE_DOOR:
            return C.COLOR_DOOR
        else:
            return C.COLOR_FLOOR

    def _draw_grid_lines(self) -> None:
        """Draw vertical and horizontal grid lines."""
        # Vertical lines
        for x in range(C.GRID_WIDTH + 1):
            px = x * C.TILE_SIZE
            pygame.draw.line(
                self.screen,
                C.COLOR_GRID_LINES,
                (px, 0),
                (px, C.WINDOW_HEIGHT),
            )
        
        # Horizontal lines
        for y in range(C.GRID_HEIGHT + 1):
            py = y * C.TILE_SIZE
            pygame.draw.line(
                self.screen,
                C.COLOR_GRID_LINES,
                (0, py),
                (C.GRID_WIDTH * C.TILE_SIZE, py),
            )

    def _draw_door(self) -> None:
        """Draw the exit door on top of the base tiles."""
        if not self.map_data:
            return
        
        dx, dy = self.map_data.door
        rect = pygame.Rect(dx * C.TILE_SIZE, dy * C.TILE_SIZE, C.TILE_SIZE, C.TILE_SIZE)
        pygame.draw.rect(self.screen, C.COLOR_DOOR, rect)

    def _draw_entities(self) -> None:
        """Draw all entities (chests and monsters) on the map."""
        if not self.map_data:
            return
        
        # Draw chests
        for cx, cy in self.map_data.chests:
            self._draw_entity_at(cx, cy, C.COLOR_CHEST)
        
        # Draw monsters
        for (mx, my) in self.map_data.monsters.keys():
            self._draw_entity_at(mx, my, C.COLOR_MONSTER)

    def _draw_entity_at(self, x: int, y: int, color: Tuple[int, int, int]) -> None:
        """Draw a single entity at the given grid coordinates."""
        rect = pygame.Rect(x * C.TILE_SIZE, y * C.TILE_SIZE, C.TILE_SIZE, C.TILE_SIZE)
        pygame.draw.rect(self.screen, color, rect)

    def _draw_player(self) -> None:
        """Draw the player character on the map."""
        rect = pygame.Rect(
            self.player.x * C.TILE_SIZE,
            self.player.y * C.TILE_SIZE,
            C.TILE_SIZE,
            C.TILE_SIZE,
        )
        pygame.draw.rect(self.screen, C.COLOR_PLAYER, rect)

    def _draw_game_over_overlay(self) -> None:
        """Draw the game over screen with restart instructions."""
        # Semi-transparent overlay
        overlay = pygame.Surface(
            (C.GRID_WIDTH * C.TILE_SIZE, C.WINDOW_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, GAME_OVER_OVERLAY_ALPHA))
        self.screen.blit(overlay, (0, 0))
        
        # Render text
        text_main = self.font.render("Game Over", True, GAME_OVER_TEXT_COLOR)
        text_restart = self.font.render("Press R to restart", True, GAME_OVER_SUBTEXT_COLOR)
        
        # Center text on screen
        center_x = (C.GRID_WIDTH * C.TILE_SIZE) // 2
        center_y = C.WINDOW_HEIGHT // 2
        
        self.screen.blit(
            text_main,
            (center_x - text_main.get_width() // 2, center_y - GAME_OVER_TEXT_OFFSET_Y),
        )
        self.screen.blit(
            text_restart,
            (center_x - text_restart.get_width() // 2, center_y + GAME_OVER_SUBTEXT_OFFSET_Y),
        )