# create q-table

# map feataures -> state

# train
# update Q value
#    calculate reward?

from pypokerengine.api.game import setup_config, start_poker
from players.learningplayer import LearningPlayer
from players.randomplayer import RandomPlayer
from players.confirmloseplayer import ConfirmLosePlayer
from players.raise_player import RaisedPlayer
from players.rvplayer import RVPlayer
import time
import atexit
import multiprocessing as mp

NUM_GAMES = 1000
MAX_ROUND = 10000
DUMP_INTERVAL = 100
GAME_COUNT = 0
window = {
    'game_count': 0
}

def exithandler(player1, player2):
    player1.write_table('p1-last-run-{}'.format(window['game_count']))
    # player2.write_table('p2-last-run-{}'.format(window['game_count']))


def init():
    config = setup_config(max_round=MAX_ROUND, initial_stack=10000, small_blind_amount=10)

    player = LearningPlayer()
    # player.load_qtable_from_file("gen-0-700-fixed.txt")
    player2 = RVPlayer()
    # player2.load_qtable_from_file("gen-0-700-fixed.txt")
    atexit.register(exithandler, player, player2)

    config.register_player(name="RVPlayer", algorithm=player2)
    config.register_player(name="learn1", algorithm=player)
    total_start_time = time.time()
    total_rounds = 0

    for i in range(NUM_GAMES):
        start_time = time.time()
        try:
            game_result = start_poker(config, verbose=0)
        except:
            print("Terminated")
            # GAME_COUNT += 1
            print(GAME_COUNT)
            break
        window['game_count'] += 1

        num_rounds = player.num_rounds_this_game
        total_rounds += num_rounds
        print("Game #{} {} rounds - {}s".format(i + 1, num_rounds, time.time() - start_time))
        print("Unseen hands: {}".format(player.unseen_hands))
        print("Unseen states: {}".format(player.unseen_states))
        print("\n".join(list(map(lambda p: "{}: {}".format(p['name'], p['stack']), game_result['players']))))
        print()
        if i > 0 and i % DUMP_INTERVAL == 0:
            player.write_table(i)


    print("Unseen hands: {}".format(player.unseen_hands))
    print("Unseen states: {}".format(player.unseen_states))
    print("Total - {} games, {} rounds, {}s".format(NUM_GAMES, total_rounds, time.time() - total_start_time))

    # for k in range(len(player.gameHistory)):
    #     game = player.gameHistory[k]
    #     print(("=" * 5 + " Game {} " + "=" * 5).format(k + 1))
    #     for n in range(len(game['action_history'])):
    #         i = game['action_history'][n]
    #         print("{:<10} {:<4} {:<2} {:<2} - {:<20} ({:<4}) {:<5} {}".format(i['street'], i['pot'], i['hole_cards'][0], i['hole_cards'][1], " ".join(i['community_cards']), i['ehs'], i['action'], i['self_raises']))
    #     # print("\n".join(list(map(lambda p: "{}: {}".format(p['name'], p['stack']), game_result['players']))))
    #     print(game['result']['name'], 'won pot of', game['pot'])
    #     print("stack sizes: {} {}".format(game['self_stack'], game['opp_stack']))

init()