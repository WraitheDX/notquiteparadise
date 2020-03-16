from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from scripts.engine import utility, entity
from scripts.engine.component import Position
from scripts.engine.core.constants import ProjectileExpiry
from scripts.engine.core.event_core import publisher
from scripts.engine.event import MoveEvent, DieEvent, ExpireEvent
from scripts.engine.library import library

if TYPE_CHECKING:
    from typing import Union, Optional, Any, Tuple, Dict, List


class AIBehaviour(ABC):
    """
    Base class for AI behaviours.
    """
    @abstractmethod
    def act(self):
        """
        Perform the behaviour
        """
        pass


class ProjectileBehaviour(AIBehaviour):
    """
    Move in direction, up to max_range (in tiles). Speed is time spent per tile moved.
    """
    def __init__(self, ent: int, direction: Tuple[int, int], max_range: int, skill_name: str):
        self.entity = ent
        self.direction = direction
        self.max_range = max_range
        self.distance_travelled = 0
        self.skill_name = skill_name

    def act(self):
        ent = self.entity

        # if we havent travelled max distance then move
        if self.distance_travelled < self.max_range:
            position = entity.get_entitys_component(ent, Position)
            projectile_data = library.get_skill_data(self.skill_name).projectile
            publisher.publish(MoveEvent(ent, (position.x, position.y), (self.direction[0], self.direction[1]),
                                        projectile_data.travel_type, projectile_data.speed))
            self.distance_travelled += 1
        else:
            # we have reached the limit, process expiry and then die
            projectile_data = library.get_skill_data(self.skill_name).projectile
            if projectile_data.expiry_type == ProjectileExpiry.ACTIVATE:
                publisher.publish(ExpireEvent(ent))
            publisher.publish(DieEvent(ent))

    # TODO -
    #  rename  interaction cause to trigger
    #  change terrain collision (everywhere) to an interaction/InteractionData
    #  introduce death interaction trigger