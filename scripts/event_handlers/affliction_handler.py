
import logging

from scripts.core.constants import GameEventTypes, AfflictionTriggers, EntityEventTypes
from scripts.event_handlers.pub_sub_hub import Subscriber, Event
from scripts.world.entity import Entity


class AfflictionHandler(Subscriber):
    """
    Handle afflictions related events
    """
    def __init__(self, event_hub):
        Subscriber.__init__(self, "affliction_handler", event_hub)

    def run(self, event):
        """
        Process events related to afflictions

        Args:
            event(Event): the event in need of processing
        """
        # log that event has been received
        logging.debug(f"{self.name} received {event.topic}:{event.event_type}...")

        if event.event_type == GameEventTypes.END_TURN:
            # trigger end of turn afflictions
            self.process_affliction_trigger(event.entity, AfflictionTriggers.END_TURN)

            # reduce duration and cleanse expired
            from scripts.global_singletons.managers import world
            world.Affliction.reduce_affliction_durations_on_entity(event.entity)
            world.Affliction.cleanse_expired_afflictions()

        elif event.event_type == EntityEventTypes.MOVE:
            self.process_affliction_trigger(event.entity, AfflictionTriggers.MOVE)
            self.process_affliction_trigger(event.entity, AfflictionTriggers.ACTION)

        elif event.event_type == EntityEventTypes.SKILL:
            self.process_affliction_trigger(event.entity, AfflictionTriggers.ACTION)

    @staticmethod
    def process_affliction_trigger(entity, trigger):
        """
        Process the required affliction trigger

        Args:
            entity (Entity):
            trigger (AfflictionTriggers):
        """
        from scripts.global_singletons.managers import world
        world.Affliction.trigger_afflictions_on_entity(trigger, entity)
