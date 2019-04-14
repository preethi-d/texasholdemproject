import sys

sys.path.insert(0, '../')
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate, _fill_community_card, \
    _pick_unused_card
from pypokerengine.engine.hand_evaluator import HandEvaluator
import multiprocessing as mp
import time
from os import getpid

table_cards_to_mapping = {}
ars_table = {}
ars_table_final = {}
ars_table_sorted = {}


# create 3 ars tables, one for flop, one for turn, one for river
def init_ars_table(ars_table, ars_table_final, ars_table_sorted, street):
    ars_table[street] = {}
    ars_table_final[street] = {}
    ars_table_sorted[street] = {}


def generate_ars_table(street, num_simulation, num_simulation_hs):
    ars_table = {}
    ars_table_final = {}
    ars_table_sorted = {}
    init_ars_table(ars_table, ars_table_final, ars_table_sorted, street)
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
            print("pid: {} street: {} round: {}".format(getpid(), street, i))

    # get average of all strengths and store it in ars_table_final
    for hand_rank_key in ars_table[street]:
        average_strength = ars_table[street][hand_rank_key]["strength"] / \
                           ars_table[street][hand_rank_key]["total_iter"]
        ars_table_final[street][hand_rank_key] = round(average_strength, 3)  # 3 dec-place

    return ars_table


def gen_wrapper(q, street, num_simulation, num_simulation_hs):
    # print("child")
    table = generate_ars_table(street, num_simulation, num_simulation_hs)
    # print(table)
    q.put(table)


def write_ars_table_to_file(filename, table):
    file = open(filename, "w+")
    for street_key in table:
        file.write(street_key + "\n")
        for hand_rank_key in sorted(table[street_key]):
            file.write(str(hand_rank_key) + " " +
                       str(table[street_key][hand_rank_key]) + "\n")


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
    return (ahead + tied / 2) / float((ahead + tied + behind))


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

if __name__ == '__main__':
    num_threads = 8
    street = 'flop'
    num_total = 1000
    num_sim_hs = 200

    if (len(sys.argv) > 1):
        print(sys.argv)
        street = sys.argv[1]
        num_total = int(sys.argv[2])
        num_sim_hs = int(sys.argv[3])
        num_threads = int(sys.argv[4])

    num_sim = int(num_total / num_threads)

    start_time = time.time()

    processes = []
    ctx = mp.get_context('spawn')
    q = ctx.Queue()

    for i in range(num_threads):
        p = ctx.Process(target=gen_wrapper,
                        args=(q, street, num_sim, num_sim_hs))
        processes.append(p)
        p.start()

    # for i in processes:
    # print(i.pid, "join waiting")
    # # i.join()
    # print(i.pid, "join done")

    sub_tables = []
    main_table = {}
    sorted_main_table = {}
    main_table[street] = {}
    sorted_main_table[street] = {}
    for i in processes:
        # print('get')
        sub_tables.append(q.get())
        # print('get q')

    for i in sub_tables:
        table = i[street]
        for score in table:
            # print(table[score])
            if score in main_table[street]:
                main_table[street][score]['strength'] += table[score]['strength']
                main_table[street][score]['total_iter'] += table[score]['total_iter']
            else:
                main_table[street][score] = {}
                main_table[street][score]['strength'] = table[score]['strength']
                main_table[street][score]['total_iter'] = table[score]['total_iter']

        for score in main_table[street]:
            sorted_main_table[street][score] = {}
            sorted_main_table[street][score] = round(
                main_table[street][score]['strength'] / float(main_table[street][score]['total_iter']), 3)

    write_ars_table_to_file('out.txt', sorted_main_table)
    end_time = time.time()
    print("{} s".format(end_time - start_time))

    # generate_ars_table(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    # get_ars_table_sorted(sys.argv[1])
    # print(main_table)
    # print(sorted_main_table)
    # write_ars_table_to_file(sys.argv[1] + "_" + sys.argv[2] + "_" + sys.argv[3] + ".txt")
