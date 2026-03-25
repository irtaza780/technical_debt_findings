import logging
import math
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Canvas and rendering constants
CANVAS_PADDING_BOTTOM = 40
HOOK_RADIUS = 10
CLAW_ANCHOR_Y = 60
CLAW_ANCHOR_OFFSET = 20

# Game state constants
DEFAULT_TIME_LIMIT = 60.0
BOMB_TIME_PENALTY = 3.0
MIN_DELTA_TIME = 0.016
FRAME_TIME_MS_DIVISOR = 1000.0

# UI constants
OVERLAY_DISPLAY_FLEX = "flex"
OVERLAY_DISPLAY_NONE = "none"
BUTTON_DISPLAY_INLINE = "inline-block"
BUTTON_DISPLAY_NONE = "none"

# Color constants
COLOR_BACKGROUND = "#0d1b2a"
COLOR_GROUND = "#2b2d42"
COLOR_ROPE = "#e0e1dd"
COLOR_HOOK = "#adb5bd"
COLOR_ANCHOR = "#e0fbfc"
COLOR_TEXT = "#ffffff"
COLOR_TEXT_DIM = "#ffffffaa"
COLOR_BORDER = "#ffffff20"
COLOR_BORDER_SEPARATOR = "#ffffff30"
COLOR_STROKE_DARK = "#00000080"

# Font constants
FONT_STATUS = "16px monospace"
FONT_INSTRUCTION = "14px monospace"
FONT_OBJECT_LABEL = "12px monospace"

# Try to import browser/pyodide APIs; fall back to headless-safe stubs
try:
    from js import document, window  # type: ignore
    from pyodide.ffi import create_proxy  # type: ignore
    PYSCRIPT = True
except ModuleNotFoundError:
    document = None
    window = None
    PYSCRIPT = False

    def create_proxy(fn):
        """Headless-safe fallback: return function as-is when PyScript unavailable."""
        return fn

from models import Claw, MineObject, distance
from level import LevelManager


class Game:
    """Main game controller for Gold Miner web game using PyScript.
    
    Manages game state, user input, physics updates, and rendering.
    Requires PyScript/browser runtime to function.
    """

    def __init__(self):
        """Initialize the game with canvas, UI elements, and game state.
        
        Raises:
            RuntimeError: If not running under PyScript/browser environment.
        """
        if not PYSCRIPT:
            raise RuntimeError("Game UI requires a browser/PyScript runtime.")

        self._initialize_canvas()
        self._initialize_ui_elements()
        self._initialize_game_state()
        self._initialize_event_handlers()
        self.start_level(self.level_index)

    def _initialize_canvas(self):
        """Set up canvas and rendering context."""
        self.canvas = document.getElementById("game-canvas")
        self.ctx = self.canvas.getContext("2d")
        self.width = self.canvas.width
        self.height = self.canvas.height
        self.ground_y = self.height - CANVAS_PADDING_BOTTOM

    def _initialize_ui_elements(self):
        """Retrieve and store references to UI elements."""
        self.overlay = document.getElementById("overlay")
        self.overlay_text = document.getElementById("overlay-text")
        self.btn_next = document.getElementById("btn-next")
        self.btn_retry = document.getElementById("btn-retry")

    def _initialize_game_state(self):
        """Initialize game state variables."""
        self.level_manager = LevelManager()
        self.level_index = 1
        self.score = 0
        self.goal = 0
        self.time_left = DEFAULT_TIME_LIMIT
        self.objects = []
        self.claw = Claw(self.width / 2, CLAW_ANCHOR_Y, self.ground_y - CLAW_ANCHOR_OFFSET)
        self.running = False
        self.level_active = True

        # Internal timing and animation frame tracking
        self._last_ts = None
        self._frame_cb = None
        self._raf_id = None
        self._transitioning = False

    def _initialize_event_handlers(self):
        """Set up event listeners with proxies to prevent garbage collection."""
        self._keydown_proxy = create_proxy(self.on_keydown)
        self._click_proxy = create_proxy(self.on_click)
        self._next_proxy = create_proxy(self.on_next)
        self._retry_proxy = create_proxy(self.on_retry)

        document.addEventListener("keydown", self._keydown_proxy)
        self.canvas.addEventListener("mousedown", self._click_proxy)
        self.btn_next.addEventListener("click", self._next_proxy)
        self.btn_retry.addEventListener("click", self._retry_proxy)

    def start(self):
        """Start the game loop via requestAnimationFrame.
        
        Idempotent: only starts a new loop if none is currently running.
        """
        if self._raf_id is not None:
            return
        self.running = True
        self.level_active = True
        self._frame_cb = create_proxy(self._loop)
        self._raf_id = window.requestAnimationFrame(self._frame_cb)

    def start_level(self, index: int):
        """Load and initialize a new level.
        
        Args:
            index: The level number to load.
        """
        cfg = self.level_manager.get_config(index, self.width, self.height, self.ground_y)
        self.level_index = index
        self.time_left = cfg["time_limit"]
        self.goal = cfg["goal_score"]
        self.objects = cfg["objects"]
        self.score = 0
        self.claw.reset()
        self.hide_overlay()
        self.running = True
        self.level_active = True
        self._last_ts = None

    def end_level(self, win: bool):
        """End the current level and display results.
        
        Args:
            win: True if level was completed successfully, False otherwise.
        """
        self._stop_game_loop()
        self._disable_buttons()
        self._transitioning = False
        self._display_level_end_overlay(win)

    def _stop_game_loop(self):
        """Stop the game loop and cancel any scheduled animation frame."""
        self.running = False
        self.level_active = False
        if self._raf_id is not None:
            try:
                window.cancelAnimationFrame(self._raf_id)
            except Exception as e:
                logger.warning(f"Failed to cancel animation frame: {e}")
            self._raf_id = None
        self._frame_cb = None

    def _disable_buttons(self):
        """Disable next and retry buttons."""
        try:
            self.btn_next.disabled = False
            self.btn_retry.disabled = False
        except Exception as e:
            logger.warning(f"Failed to update button state: {e}")

    def _display_level_end_overlay(self, win: bool):
        """Display the level end overlay with appropriate message and buttons.
        
        Args:
            win: True to show victory message, False to show failure message.
        """
        if win:
            self.overlay_text.innerText = (
                f"Level {self.level_index} Completed!\n"
                f"Score: {self.score} / Goal: {self.goal}"
            )
            self.btn_next.style.display = BUTTON_DISPLAY_INLINE
            self.btn_retry.style.display = BUTTON_DISPLAY_NONE
        else:
            self.overlay_text.innerText = (
                f"Time Up! Try Again.\n"
                f"Score: {self.score} / Goal: {self.goal}"
            )
            self.btn_next.style.display = BUTTON_DISPLAY_NONE
            self.btn_retry.style.display = BUTTON_DISPLAY_INLINE
        self.overlay.style.display = OVERLAY_DISPLAY_FLEX

    def hide_overlay(self):
        """Hide the overlay UI."""
        self.overlay.style.display = OVERLAY_DISPLAY_NONE

    def on_next(self, evt=None):
        """Handle next level button click.
        
        Args:
            evt: Optional DOM event object.
        """
        if self._transitioning:
            return
        self._transitioning = True
        self._prevent_default_event(evt)
        self._disable_buttons()
        self.level_index += 1
        self.start_level(self.level_index)
        self.start()

    def on_retry(self, evt=None):
        """Handle retry level button click.
        
        Args:
            evt: Optional DOM event object.
        """
        if self._transitioning:
            return
        self._transitioning = True
        self._prevent_default_event(evt)
        self._disable_buttons()
        self.start_level(self.level_index)
        self.start()

    def _prevent_default_event(self, evt):
        """Safely prevent default event behavior.
        
        Args:
            evt: Optional DOM event object.
        """
        if evt is not None:
            try:
                evt.preventDefault()
            except Exception as e:
                logger.debug(f"Failed to prevent default event: {e}")

    def on_keydown(self, evt):
        """Handle keyboard input for grabbing.
        
        Args:
            evt: DOM keyboard event object.
        """
        key = getattr(evt, "code", "")
        key_char = getattr(evt, "key", "")
        if key == "Space" or key_char == " " or key == "Enter":
            self._prevent_default_event(evt)
            self.claw.start_grab()

    def on_click(self, evt):
        """Handle mouse click for grabbing.
        
        Args:
            evt: DOM mouse event object.
        """
        self.claw.start_grab()

    def _loop(self, ts):
        """Main game loop callback for requestAnimationFrame.
        
        Args:
            ts: Timestamp in milliseconds from the browser.
        """
        dt = self._calculate_delta_time(ts)
        self._last_ts = ts

        if self.running:
            self.update(dt)
            self.draw()
            if self.running:
                self._raf_id = window.requestAnimationFrame(self._frame_cb)
            else:
                self._raf_id = None

    def _calculate_delta_time(self, ts):
        """Calculate time delta since last frame.
        
        Args:
            ts: Current timestamp in milliseconds.
            
        Returns:
            Delta time in seconds, minimum MIN_DELTA_TIME.
        """
        if self._last_ts is None:
            return MIN_DELTA_TIME
        return max(0.0, (ts - self._last_ts) / FRAME_TIME_MS_DIVISOR)

    def update(self, dt: float):
        """Update game state for the current frame.
        
        Args:
            dt: Delta time in seconds since last frame.
        """
        self._update_timer(dt)
        self._update_claw_and_objects(dt)
        self._check_level_transitions()

    def _update_timer(self, dt: float):
        """Update the level timer.
        
        Args:
            dt: Delta time in seconds.
        """
        if self.level_active:
            self.time_left = max(0.0, self.time_left - dt)

    def _update_claw_and_objects(self, dt: float):
        """Update claw physics and handle object collection.
        
        Args:
            dt: Delta time in seconds.
        """
        event = self.claw.update(dt, self.objects, HOOK_RADIUS)
        if event and event["type"] == "collect":
            self._handle_object_collection(event["object"])

    def _handle_object_collection(self, obj: MineObject):
        """Process the collection of an object.
        
        Args:
            obj: The collected MineObject.
        """
        if obj.kind == "bomb":
            # Bomb: negative score and time penalty
            self.score += obj.value
            self.time_left = max(0.0, self.time_left - BOMB_TIME_PENALTY)
        else:
            self.score += obj.value

    def _check_level_transitions(self):
        """Check if level should end due to time or goal completion."""
        if self.time_left <= 0.0 and self.level_active:
            won = self.score >= self.goal
            self.end_level(won)
        elif self.score >= self.goal and self.level_active:
            self.end_level(True)

    def draw(self):
        """Render the current game state to canvas."""
        self._clear_canvas()
        self._draw_background()
        self._draw_ground()
        self._draw_objects()
        self._draw_claw()
        self._draw_status_text()
        self._draw_boundaries()

    def _clear_canvas(self):
        """Clear the canvas."""
        self.ctx.clearRect(0, 0, self.width, self.height)

    def _draw_background(self):
        """Draw the background."""
        self.ctx.fillStyle = COLOR_BACKGROUND
        self.ctx.fillRect(0, 0, self.width, self.height)

    def _draw_ground(self):
        """Draw the ground area."""
        self.ctx.fillStyle = COLOR_GROUND
        self.ctx.fillRect(0, self.ground_y, self.width, self.height - self.ground_y)

    def _draw_objects(self):
        """Draw all mine objects on the canvas."""
        for obj in self.objects:
            if obj.collected:
                continue
            self._draw_single_object(obj)

    def _draw_single_object(self, obj: MineObject):
        """Draw a single mine object with labels.
        
        Args:
            obj: The MineObject to draw.
        """
        # Draw circle
        self.ctx.beginPath()
        self.ctx.arc(obj.x, obj.y, obj.r, 0, math.pi * 2)
        self.ctx.fillStyle = obj.color
        self.ctx.fill()
        self.ctx.lineWidth = 2
        self.ctx.strokeStyle = COLOR_STROKE_DARK
        self.ctx.stroke()

        # Draw value label
        self.ctx.fillStyle = COLOR_TEXT
        self.ctx.font = FONT_OBJECT_LABEL
        value_str = f"{obj.value:+d}" if obj.kind == "bomb" else f"{obj.value}"
        self.ctx.fillText(f"{obj.kind} ${value_str}", obj.x - obj.r, obj.y - obj.r - 4)

        # Draw position
        self.ctx.fillText(f"({int(obj.x)}, {int(obj.y)})", obj.x - obj.r, obj.y + obj.r + 12)

    def _draw_claw(self):
        """Draw the claw rope and hook."""
        hook_x, hook_y = self.claw.hook_position()
        self._draw_rope(hook_x, hook_y)
        self._draw_hook(hook_x, hook_y)
        self._draw_anchor()

    def _draw_rope(self, hook_x: float, hook_y: float):
        """Draw the rope from anchor to hook.
        
        Args:
            hook_x: Hook x position.
            hook_y: Hook y position.
        """
        self.ctx.beginPath()
        self.ctx.moveTo(self.claw.anchor_x, self.claw.anchor_y)
        self.ctx.lineTo(hook_x, hook_y)
        self.ctx.lineWidth = 3
        self.ctx.strokeStyle = COLOR_ROPE
        self.ctx.stroke()

    def _draw_hook(self, hook_x: float, hook_y: float):
        """Draw the hook circle.
        
        Args:
            hook_