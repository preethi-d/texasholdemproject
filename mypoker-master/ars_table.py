import sys
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate, _fill_community_card, _pick_unused_card
from pypokerengine.engine.hand_evaluator import HandEvaluator

table_cards_to_mapping = {}
ars_table = {}
ars_table_final = {}

# create 3 ars tables, one for flop, one for turn, one for river
def init_ars_table():
    for i in ["flop", "turn", "river"]:
        ars_table[i] = {}
        ars_table_final[i] = {}

def generate_ars_table(num_simulation, num_simulation_hs):
    # for flop
    for i in range(num_simulation):
        hole_card = _pick_unused_card(2, [])  # generate 2 hole cards
        community_card = _pick_unused_card(3, hole_card)  # generate 3 community cards

        # initialization of table --------------------------------------------------------------
        hand_rank = HandEvaluator.eval_hand(hole_card, community_card)  # get current hand rank
        if hand_rank not in ars_table["flop"]:
            ars_table["flop"][hand_rank] = {}
            ars_table_final["flop"][hand_rank] = {}

        hole_card_id = get_hole_card_id(hole_card)  # get unique id for hole_card
        if hole_card_id not in ars_table["flop"][hand_rank]:
            ars_table["flop"][hand_rank][hole_card_id] = {}
            ars_table["flop"][hand_rank][hole_card_id]["strength"] = 0
            ars_table["flop"][hand_rank][hole_card_id]["total_iter"] = 0
            ars_table_final["flop"][hand_rank][hole_card_id] = 0
        # end initialization of table ----------------------------------------------------------

        strength = get_hand_strength(hole_card, community_card, num_simulation_hs)  # get hand strength
        ars_table["flop"][hand_rank][hole_card_id]["strength"] += strength
        ars_table["flop"][hand_rank][hole_card_id]["total_iter"] += 1
        if i % 1000 == 0:
            print("Flop round: " + str(i) + " simulation")
    # end flop---------------------------------------------------------------------------------------------------------

    # for turn
    for j in range(num_simulation):
        hole_card = _pick_unused_card(2, [])  # generate 2 hole cards
        community_card = _pick_unused_card(4, hole_card)  # generate 4 community cards

        # initialization of table --------------------------------------------------------------
        hand_rank = HandEvaluator.eval_hand(hole_card, community_card)  # get current hand rank
        if hand_rank not in ars_table["turn"]:
            ars_table["turn"][hand_rank] = {}
            ars_table_final["turn"][hand_rank] = {}

        hole_card_id = get_hole_card_id(hole_card)  # get unique id for hole_card
        if hole_card_id not in ars_table["turn"][hand_rank]:
            ars_table["turn"][hand_rank][hole_card_id] = {}
            ars_table["turn"][hand_rank][hole_card_id]["strength"] = 0
            ars_table["turn"][hand_rank][hole_card_id]["total_iter"] = 0
            ars_table_final["turn"][hand_rank][hole_card_id] = 0
        # end initialization of table ----------------------------------------------------------

        strength = get_hand_strength(hole_card, community_card, num_simulation_hs)  # get hand strength
        ars_table["turn"][hand_rank][hole_card_id]["strength"] += strength
        ars_table["turn"][hand_rank][hole_card_id]["total_iter"] += 1
        if j % 1000 == 0:
            print("Turn round: " + str(j) + " simulation")
    # end turn---------------------------------------------------------------------------------------------------------

    # for river
    for k in range(num_simulation):
        hole_card = _pick_unused_card(2, [])  # generate 2 hole cards
        community_card = _pick_unused_card(5, hole_card)  # generate 5 community cards

        # initialization of table --------------------------------------------------------------
        hand_rank = HandEvaluator.eval_hand(hole_card, community_card)  # get current hand rank
        if hand_rank not in ars_table["river"]:
            ars_table["river"][hand_rank] = {}
            ars_table_final["river"][hand_rank] = {}

        hole_card_id = get_hole_card_id(hole_card)  # get unique id for hole_card
        if hole_card_id not in ars_table["river"][hand_rank]:
            ars_table["river"][hand_rank][hole_card_id] = {}
            ars_table["river"][hand_rank][hole_card_id]["strength"] = 0
            ars_table["river"][hand_rank][hole_card_id]["total_iter"] = 0
            ars_table_final["river"][hand_rank][hole_card_id] = 0
        # end initialization of table ----------------------------------------------------------

        strength = get_hand_strength(hole_card, community_card, num_simulation_hs)  # get hand strength
        ars_table["river"][hand_rank][hole_card_id]["strength"] += strength
        ars_table["river"][hand_rank][hole_card_id]["total_iter"] += 1
        if k % 1000 == 0:
            print("River round: " + str(k) + " simulation")
    # end river--------------------------------------------------------------------------------------------------------

    # get average of all strengths and store it in ars_table_final
    for street_key in ars_table:
        for hand_rank_key in ars_table[street_key]:
            for hole_card_id_key in ars_table[street_key][hand_rank_key]:
                average_strength = ars_table[street_key][hand_rank_key][hole_card_id_key]["strength"] /\
                                   ars_table[street_key][hand_rank_key][hole_card_id_key]["total_iter"]
                ars_table_final[street_key][hand_rank_key][hole_card_id_key] = round(average_strength, 3)  # 3 dec-place

def write_ars_table_to_file(filename):
    file = open(filename, "w+")
    for street_key in ars_table_final:
        for hand_rank_key in ars_table_final[street_key]:
            for hole_card_id_key in ars_table_final[street_key][hand_rank_key]:
                file.write(street_key + " " + str(hand_rank_key) + " " + str(hole_card_id_key) + " "
                                + str(ars_table_final[street_key][hand_rank_key][hole_card_id_key]) + "\n")

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
    return (ahead + tied/2) / (ahead + tied + behind)

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
    for card1 in cards:
        for card2 in cards:
            for suit1 in suits:
                for suit2 in suits:
                    table_cards_to_mapping[suit1 + card1][suit2 + card2] = count
                    table_cards_to_mapping[suit2 + card2][suit1 + card1] = count
        count += 1

# get the unique id that corresponds to the hole_card
def get_hole_card_id(hole_card):
    return table_cards_to_mapping[hole_card[0].__str__()][hole_card[1].__str__()]

print(sys.argv[1] + " number of simulations for ARS and " + sys.argv[2] + " number of simulations for MonteCarlo")
init_mapping_table()
generate_mapping_table()
init_ars_table()
generate_ars_table(int(sys.argv[1]), int(sys.argv[2]))
print(ars_table_final)
write_ars_table_to_file(sys.argv[1] + "_" + sys.argv[2] + ".txt")

# for each starting pair, calculate average hand strength with 3 faced up community cards for num_simulation
# times and enter into flop_table

# for each starting pair, calculate average hand strength with 4 faced up community cards for num_simulation
# times and enter into turn_table

# for each starting pair, calculate average hand strength with 5 faced up community cards for num_simulation
# times and enter into river_table
