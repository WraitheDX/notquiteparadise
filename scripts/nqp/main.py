from __future__ import annotations

import cProfile
import datetime
import io
import logging
import pstats
import time
import traceback
import sys
import pygame
import snecs
from snecs.world import default_world
from scripts.engine import state, world, chapter, key, debug
from scripts.engine.core.constants import GameState, VERSION, EventTopic
from scripts.engine.core.event_core import event_hub, publisher
from scripts.engine.event import ChangeGameStateEvent
from scripts.engine.ui.manager import ui
from scripts.nqp import processors
from scripts.nqp.entity_handler import EntityHandler
from scripts.nqp.game_handler import GameHandler
from scripts.nqp.god_handler import GodHandler
from scripts.nqp.interaction_handler import InteractionHandler
from scripts.nqp.ui_handler import UIHandler


####################################################################################################
########################## CORE DESIGN PHILOSOPHIES ##############################################
# FLOW - Periods of impetus to ensure the player is driven forward appropriately. Periods of openness to allow
# self pacing, reflection and exploration.
# TRANSPARENT - information pertinent to the player is always made available.
# COHERENT - easy to parse data, utilising a mix of art and text. Avoid need for external resource use e.g. a wiki.
# FLEXIBLE (input)- can use keyboard, mouse or controller interchangeably, with minimal difference in experience
# CUSTOMISABLE - near-core game settings can be influenced or set by the player allowing for personalisation.

########################### CODE STYLE GUIDE ####################################################
# If a function returns something, its name describes what it returns. # TODO - review
# If a function is named after a verb, its return value is of no significance or returns nothing. # TODO - review
# If checking a bool use IsA or HasA.


############################### PRE-MERGE CHECKLIST ######################################
# mypy no errors
# sphinx config pointing to correct files
# manual sphinx docs up to date
# requirement.txt up to date


####################################################################################################

def main():
    """
    The entry for the game initialisation and game loop
    """
    # initialise logging
    initialise_logging()

    # initialise profiling
    # TODO - set to turn off for production builds
    profiler = create_profiler()

    # initialise the game
    initialise_event_handlers()
    initialise_game()

    # run the game
    try:
        game_loop()
    except Exception:
        logging.critical(f"Something went wrong and killed the game loop")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for line in tb_list:
            clean_line = line.replace("\n", "")
            logging.critical(f"{clean_line}")
        traceback.print_exc()

    # we've left the game loop so now close everything down
    disable_profiling(profiler)
    dump_profiling_data(profiler)
    disable_logging()

    # print debug values
    debug.dump()

    pygame.quit()  # clean up pygame resources

    raise SystemExit  # exit window and python


def game_loop():
    """
    The core game loop, handling input, rendering and logic.
    """

    while not state.get_current() == GameState.EXIT_GAME:

        # get info to support UI updates and handling events
        delta_time = state.get_delta_time()
        current_state = state.get_current()

        # process any deletions from last frame
        snecs.process_pending_deletions(default_world)

        # have enemy take turn
        if current_state == GameState.NPC_TURN:
            # just in case the turn holder has died but not been replaced as expected
            try:
                world.take_turn(chapter.get_turn_holder())
            except AttributeError:
                chapter.rebuild_turn_queue()

        # update based on input events
        for event in pygame.event.get():
            processors.process_intent(key.convert_to_intent(event), current_state)
            ui.process_ui_events(event)

        # allow everything to update in response to new state
        processors.process_all(delta_time)
        debug.update()
        ui.update(delta_time)
        event_hub.update()
        state.update_clock()

        # show the new state
        ui.draw()


def initialise_logging():
    """
    Configure logging

    Logging levels:
        CRITICAL - A serious error, indicating that may be unable to continue running.
        ERROR - A more serious problem, has not been able to perform some function.
        WARNING - An indication that something unexpected happened, but otherwise still working as expected.
        INFO - Confirmation that things are working as expected.
        DEBUG - Detailed information, typically of interest only when diagnosing problems

    File mode options:
        'r' - open for reading(default)
        'w' - open for writing, truncating the file first
        'x' - open for exclusive creation, failing if the file already exists
        'a' - open for writing, appending to the end of the file if it exists

    """

    log_file_name = "logs/" + "game.log"
    log_level = logging.DEBUG
    file_mode = "w"

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # 8 adds space for 8 characters (# CRITICAL)
    log_format = "%(asctime)s| %(levelname)-8s| %(message)s"
    logging.basicConfig(filename=log_file_name, filemode=file_mode, level=log_level,
                        format=log_format)

    # format into uk time
    logging.Formatter.converter = time.gmtime


def create_profiler():
    """
    Create and enable the profiler
    """
    profiler = cProfile.Profile()
    profiler.enable()

    return profiler


def disable_logging():
    """
    Turn off current logging and clear logging resources
    """
    logging.shutdown()


def disable_profiling(profiler):
    """
    Turn off current profiling
    """
    profiler.disable()


def dump_profiling_data(profiler):
    """
    Dump data to a readable file
    """
    # dump the profiler stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.dump_stats("logs/profiling/profile.dump")

    # convert profiling to human readable format
    date_and_time = datetime.datetime.utcnow()
    out_stream = open("logs/profiling/" + date_and_time.strftime("%y%m%d@%H%M") + "_" + VERSION + ".profile", "w")
    ps = pstats.Stats("logs/profiling/profile.dump", stream=out_stream)
    ps.strip_dirs().sort_stats("cumulative").print_stats()


def initialise_game():
    """
    Init the game`s required info
    """
    # TODO - move to event handlers

    map_width = 50
    map_height = 30
    world.create_game_map(map_width, map_height)

    # init the player
    player = world.create_actor("player", "a desc", 1, 2, "shoom", "soft_tops",
                                 "dandy", True)

    # tell places about the player
    chapter.set_turn_holder(player)

    # create an enemy
    # TODO - remove when enemy gen is in
    enemy = world.create_actor("steve", "steve's desc", 1, 4, "goblynn", "soft_tops", "dandy")

    # create a god
    god = world.create_god("the_small_gods")

    publisher.publish(ChangeGameStateEvent(GameState.GAME_INITIALISING))


def initialise_event_handlers():
    """
    Create the various event handlers and subscribe to required events.
    """
    entity_handler = EntityHandler(event_hub)
    entity_handler.subscribe(EventTopic.ENTITY)
    entity_handler.subscribe(EventTopic.GAME)

    interaction_handler = InteractionHandler(event_hub)
    interaction_handler.subscribe(EventTopic.INTERACTION)
    interaction_handler.subscribe(EventTopic.ENTITY)

    god_handler = GodHandler(event_hub)
    god_handler.subscribe(EventTopic.ENTITY)

    ui_handler = UIHandler(event_hub)
    ui_handler.subscribe(EventTopic.ENTITY)
    ui_handler.subscribe(EventTopic.GAME)
    ui_handler.subscribe(EventTopic.UI)

    # expected last
    game_handler = GameHandler(event_hub)
    game_handler.subscribe(EventTopic.GAME)


if __name__ == "__main__":  # prevents being run from other modules
    main()