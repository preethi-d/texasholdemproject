from rvplayer import RVPlayer
import sys

sys.path.insert(0, './pypokerengine/api/')
import game

setup_config = game.setup_config
start_poker = game.start_poker
import time


t1 = float(sys.argv[1]) or 0.4
t2 = float(sys.argv[2]) or 0.5
min_change = 0.001
decay_factor = 5
rounds = 100


def sign(x):
    if x > 0: return 1
    if x < 0: return -1
    return 0


for iteration in range(1, rounds + 1):
    # Init to play 500 games of 1000 rounds
    num_game = 10
    max_round = 1000
    initial_stack = 10000
    smallblind_amount = 20

    # Setting configuration
    config = setup_config(max_round=max_round, initial_stack=initial_stack, small_blind_amount=smallblind_amount)

    # Register players
    config.register_player(name=str(t1), algorithm=RVPlayer(t1))
    config.register_player(name=str(t2), algorithm=RVPlayer(t2))

    p1total = 0
    p2total = 0
    for game in range(num_game):
        game_result = start_poker(config, verbose=0)
        # print("Game number: ", game, game_result['players'][0]['stack'], game_result['players'][1]['stack'])
        p1total += game_result['players'][0]['stack']
        p2total += game_result['players'][1]['stack']

    print("Iteration {}".format(iteration))
    print("=" * 20)
    print("P1:    {:3f}, P2:    {:3f}".format(t1, t2))
    print("P1: {:6}, P2: {:6}".format(p1total, p2total))
    if p1total > p2total:
        # p1 performed better than p2
        diff = t2 - t1
        t2 = t1 + diff/4
        t1 = t1 - diff/4
    elif p2total > p1total:
        # p1 performed better than p2
        diff = t2 - t1
        t2 = t2 + diff/4
        t1 = t2 - diff/4
