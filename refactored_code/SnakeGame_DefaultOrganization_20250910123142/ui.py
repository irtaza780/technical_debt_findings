import logging
import pygame

# Constants
DEFAULT_TEXT_COLOR = (255, 255, 255)
BUTTON_BORDER_RADIUS = 8
BUTTON_BORDER_WIDTH = 2
BUTTON_BORDER_COLOR = (100, 100, 100)
MOUSE_BUTTON_LEFT = 1

logger = logging.getLogger(__name__)


class Button:
    """
    A rectangular button widget with hover state and click detection.
    
    Attributes:
        rect (pygame.Rect): The button's position and dimensions.
        text (str): The text displayed on the button.
        font (pygame.font.Font): Font used to render the button text.
        base_color (tuple): RGB color when button is not hovered.
        hover_color (tuple): RGB color when button is hovered.
        text_color (tuple): RGB color of the button text.
    """

    def __init__(self, rect, text, font, base_color, hover_color, text_color=DEFAULT_TEXT_COLOR):
        """
        Initialize a button widget.
        
        Args:
            rect (tuple or pygame.Rect): Button position and size (x, y, width, height).
            text (str): Text to display on the button.
            font (pygame.font.Font): Font for rendering text.
            base_color (tuple): RGB color when not hovered.
            hover_color (tuple): RGB color when hovered.
            text_color (tuple, optional): RGB text color. Defaults to white.
        """
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color

    def is_hovered(self, mouse_pos):
        """
        Check if the mouse position is over the button.
        
        Args:
            mouse_pos (tuple): Mouse position as (x, y).
            
        Returns:
            bool: True if mouse is over button, False otherwise.
        """
        return self.rect.collidepoint(mouse_pos)

    def _get_current_color(self, mouse_pos):
        """
        Determine the button's current color based on hover state.
        
        Args:
            mouse_pos (tuple): Current mouse position.
            
        Returns:
            tuple: RGB color tuple for the button.
        """
        return self.hover_color if self.is_hovered(mouse_pos) else self.base_color

    def _draw_background(self, surface, color):
        """
        Draw the button background rectangle.
        
        Args:
            surface (pygame.Surface): Surface to draw on.
            color (tuple): RGB color for the background.
        """
        pygame.draw.rect(surface, color, self.rect, border_radius=BUTTON_BORDER_RADIUS)

    def _draw_border(self, surface):
        """
        Draw the button border.
        
        Args:
            surface (pygame.Surface): Surface to draw on.
        """
        pygame.draw.rect(
            surface,
            BUTTON_BORDER_COLOR,
            self.rect,
            width=BUTTON_BORDER_WIDTH,
            border_radius=BUTTON_BORDER_RADIUS
        )

    def _draw_text(self, surface):
        """
        Draw the button text centered on the button.
        
        Args:
            surface (pygame.Surface): Surface to draw on.
        """
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def draw(self, surface):
        """
        Draw the complete button (background, border, and text) on the given surface.
        
        Args:
            surface (pygame.Surface): Surface to draw the button on.
        """
        mouse_pos = pygame.mouse.get_pos()
        current_color = self._get_current_color(mouse_pos)
        
        self._draw_background(surface, current_color)
        self._draw_border(surface)
        self._draw_text(surface)

    def was_clicked(self, event, mouse_pos):
        """
        Check if the button was clicked in the given event.
        
        Args:
            event (pygame.event.EventType): The event to check.
            mouse_pos (tuple): Current mouse position.
            
        Returns:
            bool: True if button was left-clicked, False otherwise.
        """
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == MOUSE_BUTTON_LEFT
            and self.rect.collidepoint(mouse_pos)
        )


def draw_text(surface, text, font, color, center_pos):
    """
    Render and draw text centered at the specified position.
    
    Args:
        surface (pygame.Surface): Surface to draw text on.
        text (str): Text string to render.
        font (pygame.font.Font): Font to use for rendering.
        color (tuple): RGB color for the text.
        center_pos (tuple): Center position (x, y) for the text.
    """
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center_pos)
    surface.blit(text_surface, text_rect)