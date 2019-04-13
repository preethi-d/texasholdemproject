import sys
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate, _fill_community_card, _pick_unused_card
from pypokerengine.engine.hand_evaluator import HandEvaluator

table_cards_to_mapping = {}
ars_table = {}
ars_table_final = {}
ars_table_sorted = {}

# create 3 ars tables, one for flop, one for turn, one for river
def init_ars_table(street):
    ars_table[street] = {}
    ars_table_final[street] = {}
    ars_table_sorted[street] = {}

def generate_ars_table(street, num_simulation, num_simulation_hs):
    if street == 'flop':
        num_community_cards = 3
    elif street == 'turn':
        num_community_cards = 4
    elif street == 'river':
        num_community_cards = 5
    else:
        print("incorrect round name, run app again")
        return

    for i in range(num_simulation):
        hole_card = _pick_unused_card(2, [])  # generate 2 hole cards
        # generate num of community card based on street
        community_card = _pick_unused_card(num_community_cards, hole_card)

        # initialization of table --------------------------------------------------------------
        hand_rank = HandEvaluator.eval_hand(hole_card, community_card)  # get current hand rank
        if hand_rank not in ars_table[street]:
            ars_table[street][hand_rank] = {}
            ars_table_final[street][hand_rank] = {}
            ars_table[street][hand_rank]["strength"] = 0
            ars_table[street][hand_rank]["total_iter"] = 0
            ars_table_final[street][hand_rank] = 0
        # end initialization of table ----------------------------------------------------------
        strength = get_hand_strength(hole_card, community_card, num_simulation_hs)  # get hand strength
        ars_table[street][hand_rank]["strength"] += strength
        ars_table[street][hand_rank]["total_iter"] += 1

        if i % 1000 == 0:
            print(street + " round: " + str(i) + " simulation")

    # get average of all strengths and store it in ars_table_final
    for hand_rank_key in ars_table[street]:
        average_strength = ars_table[street][hand_rank_key]["strength"] / \
                           ars_table[street][hand_rank_key]["total_iter"]
        ars_table_final[street][hand_rank_key] = round(average_strength, 3)  # 3 dec-place

def write_ars_table_to_file(filename):
    file = open(filename, "w+")
    for street_key in ars_table_sorted:
        for hand_rank_key in ars_table_sorted[street_key]:
            file.write(street_key + " " + str(hand_rank_key) + " " +
                       str(ars_table_sorted[street_key][hand_rank_key]) + "\n")

def get_hand_strength(hole_card, community_card, num_simulation):
    if not community_card:
        community_card = []
    ahead_tied_behind = {'ahead': 0, 'tied': 0, 'behind': 0}

    # run monte carlo simulation for num_simulation times
    [montecarlo_simulation_hs(2, hole_card, community_card, ahead_tied_behind) for _ in range(num_simulation)]

    ahead = ahead_tied_behind['ahead']
    tied = ahead_tied_behind['tied']
    behind = ahead_tied_behind['behind']

    # return hand strength based on (ahead + tied/2) / (ahead + tied + lose)
    return (ahead + tied/2) / float((ahead + tied + behind))

# montecarlo simulation for hand strength
def montecarlo_simulation_hs(nb_player, hole_card, community_card, ahead_tied_behind):
    community_card = _fill_community_card(community_card, used_card=hole_card + community_card)
    unused_cards = _pick_unused_card((nb_player - 1) * 2, hole_card + community_card)
    opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(nb_player - 1)]

    # get rank of hole_card with the community_card that are faced up
    opponents_rank = [HandEvaluator.eval_hand(hole, community_card) for hole in opponents_hole]
    agent_rank = HandEvaluator.eval_hand(hole_card, community_card)

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

# init mapping table
def init_mapping_table():
    cards = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['H', 'S', 'D', 'C']
    for card1 in cards:
        for card2 in cards:
            for suit1 in suits:
                for suit2 in suits:
                    table_cards_to_mapping[suit1 + card1] = {}
                    table_cards_to_mapping[suit2 + card2] = {}
                    table_cards_to_mapping[suit1 + card1][suit2 + card2] = {}
                    table_cards_to_mapping[suit2 + card2][suit1 + card1] = {}

# create a 52 x 52 table that maps each pair of starting hands to their unique ids
def generate_mapping_table():
    cards = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['H', 'S', 'D', 'C']
    count = 0
    # set unique id for flipped hole_cards or hole_cards with same rank but different suits
    for card1 in range(len(cards)):
        for card2 in range(card1, len(cards), 1):
            for suit1 in suits:
                for suit2 in suits:
                    table_cards_to_mapping[suit1 + cards[card1]][suit2 + cards[card2]] = count
                    table_cards_to_mapping[suit2 + cards[card2]][suit1 + cards[card1]] = count
            count += 1

# get the unique id that corresponds to the hole_card
def get_hole_card_id(hole_card):
    return table_cards_to_mapping[hole_card[0].__str__()][hole_card[1].__str__()]

# print(sys.argv[1] + " round " + sys.argv[2] + " number of simulations for ARS and " + sys.argv[3] +
#       " number of simulations for MonteCarlo")

def get_ars_table_sorted(street):
    print(sorted(ars_table_final[street]))
    for score in sorted(ars_table_final[street]):
        ars_table_sorted[street][score] = ars_table_final[street][score]
        print(str(score) + " " + str(ars_table_sorted[street][score]))

# init_mapping_table()
# generate_mapping_table()
init_ars_table(sys.argv[1])
generate_ars_table(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
get_ars_table_sorted(sys.argv[1])
print(ars_table_sorted)
write_ars_table_to_file(sys.argv[1] + "_" + sys.argv[2] + "_" + sys.argv[3] + ".txt")
