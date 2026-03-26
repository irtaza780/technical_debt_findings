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
    """Main game controller for Gold Miner web game using PyScript."""

    def __init__(self):
        """Initialize the game with canvas, UI elements, and game state."""
        if not PYSCRIPT:
            raise RuntimeError("Game UI requires a browser/PyScript runtime.")

        self._initialize_canvas()
        self._initialize_ui_elements()
        self._initialize_game_state()
        self._register_event_handlers()
        self.start_level(self.level_index)

    def _initialize_canvas(self) -> None:
        """Set up canvas and rendering context."""
        self.canvas = document.getElementById("game-canvas")
        self.ctx = self.canvas.getContext("2d")
        self.width = self.canvas.width
        self.height = self.canvas.height
        self.ground_y = self.height - CANVAS_PADDING_BOTTOM

    def _initialize_ui_elements(self) -> None:
        """Retrieve and store references to UI elements."""
        self.overlay = document.getElementById("overlay")
        self.overlay_text = document.getElementById("overlay-text")
        self.btn_next = document.getElementById("btn-next")
        self.btn_retry = document.getElementById("btn-retry")

    def _initialize_game_state(self) -> None:
        """Initialize game state variables."""
        self.hook_radius = HOOK_RADIUS
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

    def _register_event_handlers(self) -> None:
        """Register all event handlers with DOM elements."""
        self._keydown_proxy = create_proxy(self.on_keydown)
        self._click_proxy = create_proxy(self.on_click)
        self._next_proxy = create_proxy(self.on_next)
        self._retry_proxy = create_proxy(self.on_retry)

        document.addEventListener("keydown", self._keydown_proxy)
        self.canvas.addEventListener("mousedown", self._click_proxy)
        self.btn_next.addEventListener("click", self._next_proxy)
        self.btn_retry.addEventListener("click", self._retry_proxy)

    def start(self) -> None:
        """Start the game loop if not already running."""
        if self._raf_id is not None:
            return
        self.running = True
        self.level_active = True
        self._frame_cb = create_proxy(self._loop)
        self._raf_id = window.requestAnimationFrame(self._frame_cb)

    def start_level(self, index: int) -> None:
        """Load and initialize a new level.

        Args:
            index: The level index to load.
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

    def end_level(self, win: bool) -> None:
        """End the current level and display results.

        Args:
            win: True if the player won, False otherwise.
        """
        self.running = False
        self.level_active = False
        self._cancel_animation_frame()
        self._reset_button_states()
        self._display_level_end_overlay(win)

    def _cancel_animation_frame(self) -> None:
        """Cancel the active animation frame request."""
        if self._raf_id is not None:
            try:
                window.cancelAnimationFrame(self._raf_id)
            except Exception as e:
                logger.warning(f"Failed to cancel animation frame: {e}")
            self._raf_id = None
        self._frame_cb = None

    def _reset_button_states(self) -> None:
        """Re-enable buttons and clear transitioning flag."""
        try:
            self.btn_next.disabled = False
            self.btn_retry.disabled = False
        except Exception as e:
            logger.warning(f"Failed to reset button states: {e}")
        self._transitioning = False

    def _display_level_end_overlay(self, win: bool) -> None:
        """Display the level end overlay with appropriate message and buttons.

        Args:
            win: True if the player won, False otherwise.
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

    def hide_overlay(self) -> None:
        """Hide the overlay UI."""
        self.overlay.style.display = OVERLAY_DISPLAY_NONE

    def on_next(self, evt=None) -> None:
        """Handle next level button click.

        Args:
            evt: The click event (optional).
        """
        if self._transitioning:
            return
        self._transitioning = True
        self._prevent_default_event(evt)
        self._disable_buttons()
        self.level_index += 1
        self.start_level(self.level_index)
        self.start()

    def on_retry(self, evt=None) -> None:
        """Handle retry level button click.

        Args:
            evt: The click event (optional).
        """
        if self._transitioning:
            return
        self._transitioning = True
        self._prevent_default_event(evt)
        self._disable_buttons()
        self.start_level(self.level_index)
        self.start()

    def _prevent_default_event(self, evt) -> None:
        """Prevent default event behavior if event exists.

        Args:
            evt: The event object (optional).
        """
        if evt is not None:
            try:
                evt.preventDefault()
            except Exception as e:
                logger.debug(f"Failed to prevent default event: {e}")

    def _disable_buttons(self) -> None:
        """Disable next and retry buttons."""
        try:
            self.btn_next.disabled = True
            self.btn_retry.disabled = True
        except Exception as e:
            logger.warning(f"Failed to disable buttons: {e}")

    def on_keydown(self, evt) -> None:
        """Handle keyboard input for grabbing.

        Args:
            evt: The keyboard event.
        """
        key = getattr(evt, "code", "")
        key_char = getattr(evt, "key", "")
        if key == "Space" or key_char == " " or key == "Enter":
            self._prevent_default_event(evt)
            self.claw.start_grab()

    def on_click(self, evt) -> None:
        """Handle mouse click for grabbing.

        Args:
            evt: The mouse event.
        """
        self.claw.start_grab()

    def _loop(self, ts: float) -> None:
        """Main game loop callback.

        Args:
            ts: Timestamp from requestAnimationFrame.
        """
        dt = self._calculate_delta_time(ts)
        if self.running:
            self.update(dt)
            self.draw()
            if self.running:
                self._raf_id = window.requestAnimationFrame(self._frame_cb)
            else:
                self._raf_id = None

    def _calculate_delta_time(self, ts: float) -> float:
        """Calculate delta time since last frame.

        Args:
            ts: Current timestamp in milliseconds.

        Returns:
            Delta time in seconds.
        """
        if self._last_ts is None:
            dt = MIN_DELTA_TIME
        else:
            dt = max(0.0, (ts - self._last_ts) / FRAME_TIME_MS_DIVISOR)
        self._last_ts = ts
        return dt

    def update(self, dt: float) -> None:
        """Update game state.

        Args:
            dt: Delta time since last update in seconds.
        """
        self._update_timer(dt)
        self._update_claw_and_objects(dt)
        self._check_level_transitions()

    def _update_timer(self, dt: float) -> None:
        """Update the game timer.

        Args:
            dt: Delta time in seconds.
        """
        if self.level_active:
            self.time_left = max(0.0, self.time_left - dt)

    def _update_claw_and_objects(self, dt: float) -> None:
        """Update claw position and handle object collection.

        Args:
            dt: Delta time in seconds.
        """
        event = self.claw.update(dt, self.objects, self.hook_radius)
        if event and event["type"] == "collect":
            self._handle_object_collection(event["object"])

    def _handle_object_collection(self, obj: MineObject) -> None:
        """Handle the collection of an object.

        Args:
            obj: The collected object.
        """
        if obj.kind == "bomb":
            # Bomb: negative score and time penalty
            self.score += obj.value
            self.time_left = max(0.0, self.time_left - BOMB_TIME_PENALTY)
        else:
            self.score += obj.value

    def _check_level_transitions(self) -> None:
        """Check if level should end and trigger appropriate transition."""
        if self.time_left <= 0.0 and self.level_active:
            won = self.score >= self.goal
            self.end_level(won)
        elif self.score >= self.goal and self.level_active:
            self.end_level(True)

    def draw(self) -> None:
        """Render the current game state."""
        self._draw_background()
        self._draw_objects()
        self._draw_claw()
        self._draw_status_text()
        self._draw_boundaries()

    def _draw_background(self) -> None:
        """Draw background and ground."""
        ctx = self.ctx
        ctx.clearRect(0, 0, self.width, self.height)
        ctx.fillStyle = COLOR_BACKGROUND
        ctx.fillRect(0, 0, self.width, self.height)
        ctx.fillStyle = COLOR_GROUND
        ctx.fillRect(0, self.ground_y, self.width, self.height - self.ground_y)

    def _draw_objects(self) -> None:
        """Draw all mine objects on the canvas."""
        for obj in self.objects:
            if obj.collected:
                continue
            self._draw_single_object(obj)

    def _draw_single_object(self, obj: MineObject) -> None:
        """Draw a single mine object with label and position.

        Args:
            obj: The object to draw.
        """
        ctx = self.ctx
        # Draw circle
        ctx.beginPath()
        ctx.arc(obj.x, obj.y, obj.r, 0, math.pi * 2)
        ctx.fillStyle = obj.color
        ctx.fill()
        ctx.lineWidth = 2
        ctx.strokeStyle = COLOR_STROKE_DARK
        ctx.stroke()

        # Draw value label
        ctx.fillStyle = COLOR_TEXT
        ctx.font = FONT_OBJECT_LABEL
        val = f"{obj.value:+d}" if obj.kind == "bomb" else f"{obj.value}"
        ctx.fillText(f"{obj.kind} ${val}", obj.x - obj.r, obj.y - obj.r - 4)

        # Draw position
        ctx.fillText(f"({int(obj.x)}, {int(obj.y)})", obj.x - obj.r, obj.y + obj.r + 12)

    def _draw_claw(self) -> None:
        """Draw claw rope, hook, and anchor."""
        hook_x, hook_y = self.claw.hook_position()
        self._draw_rope(hook_x, hook_y)
        self._draw_hook(hook_x, hook_y)
        self._draw_anchor()

    def _draw_rope(self, hook_x: float, hook_y: float) -> None:
        """Draw the rope from anchor to hook.

        Args:
            hook_x: Hook x position.
            hook_y: Hook y position.
        """
        ctx = self.ctx
        ctx.beginPath()
        ctx.moveTo(self.claw.anchor_x, self.claw.anchor_y)
        ctx.lineTo(hook_x, hook_y)
        ctx.lineWidth = 3
        ctx.strokeStyle = COLOR_ROPE
        ctx.stroke()

    def _draw_hook(self, hook_x: float, hook_y: float) -> None:
        """Draw the hook at the end of the rope.

        Args:
            hook_x: Hook x position.
            hook_y: Hook y position.
        """
        ctx = self.ctx