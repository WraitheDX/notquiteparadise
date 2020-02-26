from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any
import logging
import pygame
from scripts.core.constants import PrimaryStatTypes, TILE_SIZE, ENTITY_BLOCKS_SIGHT, ICON_SIZE, IMAGE_NOT_FOUND_PATH
from scripts.core.library import library
from scripts.managers.game_manager.game_manager import game
from scripts.world.components import IsPlayer, Position, Resources, Race, Savvy, Homeland, Knowledge, Identity, \
    Aesthetic, IsGod, Opinion, HasCombatStats, Blocking
from scripts.world.tile import Tile
from scripts.world.combat_stats import CombatStats

if TYPE_CHECKING:
    from typing import List, Union, Dict, Tuple
    from scripts.managers.world_manager.world_manager import WorldManager


class EntityMethods:
    """
    Queries relating to entities.

    Attributes:
        manager(WorldManager): the manager containing this class.
    """

    def __init__(self, manager):
        self._manager = manager  # type: WorldManager

    ############### GET ###################

    def get_player(self) -> Union[int, None]:
        """
        Get the player.

        Returns:
            int: Entity ID
        """
        for entity, flag in self._manager.World.get_component(IsPlayer):
            return entity
        return None

    def get_entity(self, unique_component) -> Union[int, None]:
        """
        Get a single entity that has a component. If multiple entities have the given component only the first found
        is returned.

        Args:
            unique_component ():

        Returns:
            int: Entity ID.
        """
        entities = []
        for entity, flag in self._manager.World.get_component(unique_component):
            entities.append(entity)

        num_entities = len(entities)

        if num_entities > 1:
            logging.warning(f"Tried to get an entity with {unique_component} component but found {len(entities)} "
                            f"entities with that component.")
        elif num_entities == 0:
            logging.warning(f"Tried to get an entity with {unique_component} component but found none.")
            return None

        return entities[0]

    def get_entities(self, component1, component2=None, component3=None) -> List[int]:
        """
        Get entities with the specified components.

        Args:
            component1 ():
            component2 ():
            component3 ():

        Returns:
            List[int]: List of Entity IDs
        """
        entities = []

        if not component2 and not component3:
            for entity, c1 in self._manager.World.get_component(component1):
                entities.append(entity)
        elif component2 and not component3:
            for entity, (c1, c2) in self._manager.World.get_components(component1, component2):
                entities.append(entity)
        elif component2 and component3:
            for entity, (c1, c2, c3) in self._manager.World.get_components(component1, component2, component3):
                entities.append(entity)

        return entities

    def get_entities_and_components_in_area(self, area: List[Tile], component1=None, component2=None,
            component3=None) -> Dict:
        """
        Return a list of entities and their specified components, plus Position. e.g. (Position, component1). If no
        components are specified the return will be (Position, None).

        N.B. Do not specify Position as a component.

        Args:
            area ():
            component1 ():
            component2 ():
            component3 ():

        Returns:

        """
        entities = {}

        if not component1 and not component2 and not component3:
            for entity, pos in self._manager.World.get_component(Position):
                for tile in area:
                    if tile.x == pos.x and tile.y == pos.y:
                        entities[entity] = (pos, None)
        elif component1 and not component2 and not component3:
            for entity, (pos, c1) in self._manager.World.get_components(Position, component1):
                for tile in area:
                    if tile.x == pos.x and tile.y == pos.y:
                        entities[entity] = (pos, c1)
        elif component1 and component2 and not component3:
            for entity, (pos, c1, c2) in self._manager.World.get_components(Position, component1, component2):
                for tile in area:
                    if tile.x == pos.x and tile.y == pos.y:
                        entities[entity] = (pos, c1, c2)
        elif component1 and component2 and component3:
            for entity, (pos, c1, c2, c3) in self._manager.World.get_components(Position, component1, component2,
                                                                                component3):
                for tile in area:
                    if tile.x == pos.x and tile.y == pos.y:
                        entities[entity] = (pos, c1, c2, c3)

        return entities

    def get_component(self, entity, component):
        """
        Get an entity's component.

        Args:
            entity ():
            component ():

        Returns:

        """
        if self._manager.World.has_component(entity, component):
            return self._manager.World.component_for_entity(entity, component)
        else:
            return None

    def get_components(self, entity) -> Tuple:
        """
        Get all of an entity's components.

        Args:
            entity ():

        Returns:

        """
        return self._manager.World.components_for_entity(entity)

    def get_identity(self, entity: int) -> Identity:
        """Get an entity's Identity component."""

        return self.get_component(entity, Identity)

    @staticmethod
    def get_combat_stats(entity: int) -> CombatStats:
        """
        Create and return a stat object  for an entity.

        Args:
            entity ():

        Returns:

        """
        return CombatStats(entity)

    def get_primary_stat(self, entity: int, primary_stat: PrimaryStatTypes) -> int:
        """
        Get an entity's primary stat.
        """
        stat = primary_stat
        value = 0

        for people in self._manager.World.try_component(entity, Race):
            people_data = library.get_people_data(people.name)
            value += getattr(people_data, stat)

        for savvy in self._manager.World.try_component(entity, Savvy):
            savvy_data = library.get_savvy_data(savvy.name)
            value += getattr(savvy_data, stat)

        for homeland in self._manager.World.try_component(entity, Homeland):
            homeland_data = library.get_homeland_data(homeland.name)
            value += getattr(homeland_data, stat)

        # TODO - re add afflicitons
        # value += self._manager.Affliction.get_stat_change_from_afflictions_on_entity(entity, primary_stat)

        # ensure no dodgy numbers, like floats or negative
        value = max(1, int(value))

        return value

    ############## QUERIES  ################

    def has_component(self, entity, component):
        """
        Confirm if an entity has a component

        Args:
            entity ():
            component ():

        Returns:

        """
        if self._manager.World.has_component(entity, component):
            return True
        else:
            return False

    ############## ENTITY EXISTENCE ################

    def create(self, components: List = []) -> int:
        """
        Use each component in a list of components to create an entity

        Args:
            components ():
        """
        world = self._manager.World
        entity = world.create_entity()

        for component in components:
            world.add_component(entity, component)

        return entity

    def delete(self, entity: int):
        """
        Queues entity for removal from the world. Happens at the next run of World.process.

        Args:
            entity:
        """
        if entity:
            self._manager.World.delete_entity(entity)
            logging.info(f"Entity ({entity}) deleted.")
        else:
            logging.error("Tried to delete an entity but entity was None.")

    def create_god(self, god_name: str) -> int:
        """
        Create an entity with all of the components to be a god.

        Args:
            god_name (): god_name must be in the gods json file.

        Returns:
            int: Entity ID
        """
        data = library.get_god_data(god_name)
        god = []

        # get aesthetic info
        sprite = game.Utility.get_image(data.sprite, (TILE_SIZE, TILE_SIZE))
        icon = game.Utility.get_image(data.sprite, (TILE_SIZE, TILE_SIZE))

        # get knowledge info
        interventions = data.interventions
        intervention_names = []
        for name, intervention in interventions.items():
            intervention_names.append(intervention.skill_key)

        god.append(Identity(data.name, data.description))
        god.append(Aesthetic(sprite, icon))
        god.append(IsGod())
        god.append(Opinion())
        god.append(Knowledge(intervention_names))
        god.append((Resources(9999, 9999)))
        entity = self._manager.Entity.create(god)

        return entity

    def create_actor(self, name: str, description: str, x: int, y: int, people_name: str, homeland_name: str,
            savvy_name: str, is_player: bool = False) -> int:
        """
        Create an entity with all of the components to be an actor. is_player is Optional and defaults to false.
        Returns Entity ID.
        """
        actor = []

        # player components
        if is_player:
            actor.append(IsPlayer())

        # actor components
        actor.append(Identity(name, description))
        actor.append(Position(x, y))  # TODO - check position not blocked before spawning
        actor.append(HasCombatStats())
        actor.append(Blocking(True, ENTITY_BLOCKS_SIGHT))
        actor.append(Race(people_name))
        actor.append(Homeland(homeland_name))
        actor.append(Savvy(savvy_name))

        entity = self.create(actor)

        # give full resources
        stats = self.get_combat_stats(entity)
        self._manager.World.add_component(entity, Resources(stats.max_hp, stats.max_stamina))

        # get skills from characteristics
        known_skills = ["basic_attack"]  # N.B. All actors start with basic attack
        people_data = library.get_people_data(people_name)
        if people_data.known_skills != ["none"]:
            known_skills += people_data.known_skills

        homeland_data = library.get_homeland_data(homeland_name)
        if homeland_data.known_skills != ["none"]:
            known_skills += homeland_data.known_skills

        savvy_data = library.get_savvy_data(savvy_name)
        if savvy_data.known_skills != ["none"]:
            known_skills += savvy_data.known_skills

        # add skills to entity
        self._manager.World.add_component(entity, Knowledge(known_skills))

        # add aesthetic
        icon = game.Utility.get_image(people_data.sprite, (ICON_SIZE, ICON_SIZE))
        homeland_sprite = game.Utility.get_image(homeland_data.sprite, (TILE_SIZE, TILE_SIZE))
        people_sprite = game.Utility.get_image(people_data.sprite, (TILE_SIZE, TILE_SIZE))
        savvy_sprite = game.Utility.get_image(savvy_data.sprite, (TILE_SIZE, TILE_SIZE))

        # combine the sprite homeland -> people -> savvy
        homeland_sprite.blits(((people_sprite, (0, 0)), (savvy_sprite, (0, 0))))

        self._manager.World.add_component(entity, Aesthetic(homeland_sprite, icon))

        # player fov
        if is_player:
            self._manager.FOV.recompute_player_fov(x, y, stats.sight_range)

        return entity

    ############### COMPONENT ACTIONS ##########

    def spend_time(self, entity: int, time_spent: int):
        """
        Add time_spent to the entity's total time spent.

        Args:
            entity ():
            time_spent ():
        """
        if entity:
            resources = self._manager.World.component_for_entity(entity, Resources)
            resources.time_spent += time_spent
        else:
            logging.error("Tried to spend entity's time but entity was None.")

    def learn_skill(self, entity: int, skill_name: str):
        """
        Add the skill name to the entity's knowledge component.

        Args:
            entity ():
            skill_name ():
        """
        if not self._manager.World.has_component(entity, Knowledge()):
            self._manager.World.add_component(entity, Knowledge())

        knowledge = self.get_component(entity, Knowledge())
        knowledge.skills.append(skill_name)

    def judge_action(self, entity: int, action: Any):
        """
        Have all entities alter opinions of the entity based on the action taken, if they have an attitude towards
        that  action.

        Args:
            entity ():
            action (): Can be str if matching name, e.g. affliction name, or class, e.g. Hit Type name.

        """

        for ent, (is_god, opinion, identity) in self._manager.World.get_components(IsGod, Opinion, Identity):

            attitudes = library.get_god_attitudes_data(identity.name)

            action_name = action

            # check if the god has an attitude towards the action and apply the opinion change,
            # adding the entity to the dict if necessary
            if action_name in attitudes:
                if entity in opinion.opinions:
                    opinion.opinions[entity] += attitudes[action_name].opinion_change
                else:
                    opinion.opinions[entity] = attitudes[action_name].opinion_change

                entity_identity = self.get_identity(entity)
                logging.info(f"'{identity.name}' reacted to '{entity_identity.name}' using {action_name}.  New "
                             f"opinion = {opinion.opinions[entity]}")

    def consider_intervening(self, entity: int, action: Any) -> List[Tuple[str, int]]:
        """
        Have all entities consider intervening

        Args:
            entity (): entity who acted
            action (object): Can be str if matching name, e.g. affliction name, or class attribute, e.g. Hit Type name.

        Returns:
            List[Tuple]: List of tuples containing (god_entity_id, intervention name).
        """
        chosen_interventions = []
        desire_to_intervene = 10
        desire_to_do_nothing = 75  # weighting for doing nothing # TODO - move magic number to config

        for ent, (is_god, opinion, identity, knowledge) in self._manager.World.get_components(IsGod, Opinion,
                                                                                              Identity, Knowledge):
            attitudes = library.get_god_attitudes_data(identity.name)

            action_name = action

            # check if the god has an attitude towards the action and increase likelihood of intervening
            if action_name in attitudes:
                desire_to_intervene = 30

            # get eligible interventions and their weightings. Need separate lists for random.choices
            eligible_interventions = []
            intervention_weightings = []
            for intervention_name in knowledge.skills:
                intervention_data = library.get_god_intervention_data(identity.name, intervention_name)

                # is the god willing to intervene i.e. does the opinion score meet the required opinion
                opinion_score = opinion.opinions[entity]
                required_opinion = intervention_data.required_opinion
                # check if greater or lower, depending on whether required opinion is positive or negative
                if 0 <= required_opinion < opinion_score:
                    amount_exceeding_requirement = opinion_score - required_opinion

                    eligible_interventions.append(intervention_name)
                    intervention_weightings.append(amount_exceeding_requirement)

                elif 0 > required_opinion > opinion_score:
                    amount_exceeding_requirement = required_opinion - opinion_score  # N.B. opposite to above
                    eligible_interventions.append(intervention_name)
                    intervention_weightings.append(amount_exceeding_requirement)

            # add chance to do nothing
            eligible_interventions.append("Nothing")
            intervention_weightings.append(desire_to_do_nothing - desire_to_intervene)

            # which intervention, if any, shall the god consider using?
            chosen_intervention,  = random.choices(eligible_interventions, intervention_weightings)
            # N.B. use , to unpack the result

            # if god has chosen to take an action then add to list
            if chosen_intervention != "Nothing":
                chosen_interventions.append((ent, chosen_intervention))

        return chosen_interventions

