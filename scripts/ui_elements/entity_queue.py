
import logging
import pygame

from typing import List, Tuple
from scripts.core.constants import VisualInfo
from scripts.core.fonts import Font
from scripts.ui_elements.palette import Palette
from scripts.ui_elements.templates.panel import Panel


class EntityQueue:
    def __init__(self):
        # setup info
        self.font = Font().entity_queue
        self.palette = Palette().entity_queue
        self.entity_icon_size = 64
        self.entity_queue = []  # type: List[Tuple]  # (image, str)
        self.gap_between_entities = 2

        # panel info
        panel_width = int(self.entity_icon_size * 1.5)
        panel_height = int(VisualInfo.BASE_WINDOW_HEIGHT / 2)
        panel_x = VisualInfo.BASE_WINDOW_WIDTH - (panel_width * 2)
        panel_y = 0
        panel_border = 2
        panel_background_colour = self.palette.background
        panel_border_colour = self.palette.border
        self.panel = Panel(panel_x, panel_y, panel_width, panel_height, panel_background_colour, panel_border,
                           panel_border_colour)

        # defined here due to dependency on panel
        self.max_entities_to_show = int(panel_height / (self.entity_icon_size + self.gap_between_entities))

        # get entities to show
        self.update_entity_queue()

        # set self to be rendered
        from scripts.global_singletons.managers import ui_manager
        ui_manager.update_panel_visibility("entity_queue", self, True)

        logging.debug(f"EntityQueue initialised.")

    def draw(self, surface):
        """
        Draw the entity queue

        Args:
            surface:
        """

        # panel background
        self.panel.draw_background()

        panel_surface = self.panel.surface
        x = int(self.panel.width / 4) - 5  # draw to centre
        y = 10

        for entity_icon, entity_name in self.entity_queue:
            panel_surface.blit(entity_icon, (x, y))
            self.font.render_to(panel_surface, (x, y), entity_name, self.palette.text_default)

            y += self.entity_icon_size + self.gap_between_entities

        # panel border
        self.panel.draw_border()

        # draw everything to the passed in surface
        surface.blit(self.panel.surface, (self.panel.x, self.panel.y))

    def update_entity_queue(self):
        """
        Get info from the turn_manager and update the entity queue to be displayed
        """
        # clear current queue
        self.entity_queue.clear()

        counter = 0

        # loop entities in turn queue, up to max to show
        from scripts.global_singletons.managers import turn_manager
        for entity, time in turn_manager.turn_queue.items():
            if counter < self.max_entities_to_show:
                icon = entity.icon
                # catch any images not the right size and resize them
                if icon.get_size() != (self.entity_icon_size, self.entity_icon_size):
                    icon = pygame.transform.smoothscale(icon, (self.entity_icon_size, self.entity_icon_size))

                self.entity_queue.append((icon, entity.name))

                counter += 1

            else:
                break