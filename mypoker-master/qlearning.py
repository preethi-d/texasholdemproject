# create q-table

# map feataures -> state

# train
# update Q value
#    calculate reward?

from pypokerengine.api.game import setup_config, start_poker
from consoleplayer import ConsolePlayer
from rvplayer import RVPlayer
from learningplayer import LearningPlayer
from randomplayer import RandomPlayer


def init():
    print("hello world")
    qtable = make_table()
    config = setup_config(max_round=100, initial_stack=10000, small_blind_amount=10)

    player = LearningPlayer()

    config.register_player(name="rand", algorithm=RandomPlayer())
    config.register_player(name="learn", algorithm=player)

    game_result = start_poker(config, verbose=1)
    for k in range(len(player.gameHistory)):
        game = player.gameHistory[k]
        print(("=" * 5 + " Game {} " + "=" * 5).format(k + 1))
        for n in range(len(game['action_history'])):
            i = game['action_history'][n]
            print(("{:<10} {:<4} {:<2} {:<2} - {:<20} {:<5}").format(i['street'], i['pot'], i['hole_cards'][0], i['hole_cards'][1], " ".join(i['community_cards']), i['action']))
        # print("\n".join(list(map(lambda p: "{}: {}".format(p['name'], p['stack']), game_result['players']))))
        print(game['result']['name'], 'won pot of', game['pot'])
        print("stack sizes: {} {}".format(game['self_stack'], game['opp_stack']))


def make_table():
    return {}
    pass


def get_state(ehs, pot_size, opp_play_style, opp_num_raises, self_raises, current_street):
    return ""
    pass


def train(n):
    pass


def train_round(epsilon):
    # set up emulator
    # run the thing
    # update weights

    pass


def get_hand_strength(self, hole_card, community_card, num_simulation):
    if not community_card:
        community_card = []
    community_card = gen_cards(community_card)
    hole_card = gen_cards(hole_card)
    agent_rank = HandEvaluator.eval_hand(hole_card, community_card)
    ahead_tied_behind = {'ahead': 0, 'tied': 0, 'behind': 0}

    # run monte carlo simulation for num_simulation times
    [self.montecarlo_simulation_hs(2, hole_card, community_card, ahead_tied_behind, agent_rank) for _ in
     range(num_simulation)]

    ahead = ahead_tied_behind['ahead']
    tied = ahead_tied_behind['tied']
    behind = ahead_tied_behind['behind']

    # return hand strength based on (ahead + tied/2) / (ahead + tied + lose)
    return (ahead + tied / 2) / (ahead + tied + behind)


def get_hand_potential(self, hole_card, community_card, num_simulation):
    hole_card = gen_cards(hole_card)
    community_card = gen_cards(community_card)
    agent_rank = HandEvaluator.eval_hand(hole_card, community_card)

    hand_potential = {'ahead': {'ahead': 0, 'tied': 0, 'behind': 0},
                      'tied': {'ahead': 0, 'tied': 0, 'behind': 0},
                      'behind': {'ahead': 0, 'tied': 0, 'behind': 0}}
    total_hand_potential = {'ahead': 0, 'tied': 0, 'behind': 0}
    [self.montecarlo_simulation_hp(2, hole_card, community_card, hand_potential,
                                   total_hand_potential, agent_rank, num_simulation) for _ in range(num_simulation)]
    ppot = (hand_potential['behind']['ahead']
            + (hand_potential['behind']['tied'] / 2)
            + (hand_potential['tied']['ahead'] / 2)) / (total_hand_potential['behind']
                                                        + (total_hand_potential['tied'] / 2)
                                                        + 0.000000001)
    npot = (hand_potential['ahead']['behind']
            + (hand_potential['tied']['behind'] / 2)
            + (hand_potential['ahead']['tied'] / 2)) / (total_hand_potential['ahead']
                                                        + (total_hand_potential['tied'] / 2)
                                                        + 0.000000001)
    return ppot, npot


# montecarlo simulation for hand strength
def montecarlo_simulation_hs(self, nb_player, hole_card, community_card, ahead_tied_behind, agent_rank):
    community_card = _fill_community_card(community_card, used_card=hole_card + community_card)
    unused_cards = _pick_unused_card((nb_player - 1) * 2, hole_card + community_card)
    opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(nb_player - 1)]

    # get rank of hole_card with the community_card that are faced up
    opponents_rank = [HandEvaluator.eval_hand(hole, community_card) for hole in opponents_hole]

    if agent_rank > max(opponents_rank):
        # if win add increment ahead
        ahead_tied_behind['ahead'] += 1
    elif agent_rank == max(opponents_rank):
        # if tie increment tied
        ahead_tied_behind['tied'] += 1
    else:
        # if lose increment behind
        ahead_tied_behind['behind'] += 1
    # print(ahead_tied_behind)


# montecarlo simulation for hand potential
def montecarlo_simulation_hp(self, nb_player, hole_card, community_card, hp, total_hp, agent_rank, num_simulation):
    unused_cards = _pick_unused_card((nb_player - 1) * 2, hole_card + community_card)
    opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(nb_player - 1)]

    # get rank of hole_card with the community_card that are faced up
    opponents_rank = [HandEvaluator.eval_hand(hole, community_card) for hole in opponents_hole]

    index = 'ahead'
    if agent_rank > max(opponents_rank):
        index = 'ahead'
    elif agent_rank == max(opponents_rank):
        index = 'tied'
    else:
        index = 'behind'
    total_hp[index] += 1

    for i in range(num_simulation):
        all_community_cards = _fill_community_card(community_card, used_card=hole_card + community_card)
        agent_best_rank = HandEvaluator.eval_hand(hole_card, all_community_cards)
        opp_best_rank = HandEvaluator.eval_hand(hole_card, all_community_cards)
        if agent_best_rank > opp_best_rank:
            hp[index]['ahead'] += (1 / num_simulation)  # normalize so that output of ppot and npot is from 0 to 1
        elif agent_best_rank == opp_best_rank:
            hp[index]['tied'] += (1 / num_simulation)  # normalize so that output of ppot and npot is from 0 to 1
        else:
            hp[index]['behind'] += (1 / num_simulation)  # normalize so that output of ppot and npot is from 0 to 1

init()