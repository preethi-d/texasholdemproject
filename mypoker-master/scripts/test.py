from pypokerengine.api.game import setup_config, start_poker
from players.consoleplayer import ConsolePlayer
from players.rvplayer import RVPlayer

#TODO:config the config as our wish
config = setup_config(max_round=10, initial_stack=10000, small_blind_amount=10)



config.register_player(name="console", algorithm=ConsolePlayer())
config.register_player(name="rv", algorithm=RVPlayer())


game_result = start_poker(config, verbose=1)
