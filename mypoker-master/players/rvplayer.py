from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.utils.card_utils import _fill_community_card, _pick_unused_card, gen_cards
import datetime

class RVPlayer(BasePokerPlayer):

    winrates = {}
    opp_num_raises = 0
    opp_num_calls = 0
    opp_num_folds = 0
    self_raises = 0
    opp_uuid = ''
    num_rounds_played = 0

    def __init__(self, threshold = 0.5):
        super(BasePokerPlayer, self).__init__()
        f = open("hs_data/handstr.txt")
        cards = ["A"] + [str(i) for i in range(2, 10)] + ["T", "J", "Q", "K"]
        # print(cards)
        for i in cards:
            self.winrates[i] = {}

        for i in f:
            c1, c2, n = i.strip().split(" ")
            self.winrates[c1][c2] = n
            self.winrates[c2][c1] = n

        self.threshold = threshold

    def get_hand_strength(self, hole_card, community_card, num_simulation):
        if not community_card:
            community_card = []
        community_card = gen_cards(community_card)
        hole_card = gen_cards(hole_card)
        agent_rank = HandEvaluator.eval_hand(hole_card, community_card)
        ahead_tied_behind = {'ahead': 0, 'tied': 0, 'behind': 0}

        # run monte carlo simulation for num_simulation times
        [self.montecarlo_simulation_hs(2, hole_card, community_card, ahead_tied_behind, agent_rank) for _ in range(num_simulation)]

        ahead = ahead_tied_behind['ahead']
        tied = ahead_tied_behind['tied']
        behind = ahead_tied_behind['behind']

        # return hand strength based on (ahead + tied/2) / (ahead + tied + lose)
        return (ahead + tied/2) / (ahead + tied + behind)

    def get_opponent_hand_strength(self, hole_card, community_card):
        unused_cards = _pick_unused_card(2, hole_card+community_card)

        # get 100 possibilities of opponent's hole
        opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(1)]

        # calculate the total score of opponent's hand based on the 100 possibilities of opponent's hole
        opponents_score = 0
        for hole in opponents_hole:
            opponents_score += HandEvaluator.eval_hand(hole, community_card)
        opponents_avg_score = opponents_score/opponents_hole.__sizeof__()
        return opponents_avg_score

    def get_opponent_play_style(self):
        aggressive_factor = self.opp_num_raises/(self.opp_num_calls + 0.000000001)  # to prevent divide by 0
        player_tightness = self.opp_num_folds/self.num_rounds_played

        if aggressive_factor > 1 and player_tightness < 0.28:
            return 'conservative/aggressive'
        elif aggressive_factor > 1 and player_tightness >= 0.28:
            return 'loose/aggressive'
        elif aggressive_factor <= 1 and player_tightness < 0.28:
            return 'conservative/passive'
        else:
            return 'conservative/loose'

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

    def construct_ars(self, nb_player, num_simulation):
        num_rows = 255
        num_cols = 9
        num_unique_starting_pair = 169
        # create 3 ars tables, one for flop, one for turn, one for river
        flop_table = [[[0 for k in range(num_unique_starting_pair)]for j in range(num_cols)]for i in range(num_rows)]
        turn_table = [[[0 for k in range(num_unique_starting_pair)]for j in range(num_cols)]for i in range(num_rows)]
        river_table = [[[0 for k in range(num_unique_starting_pair)]for j in range(num_cols)]for i in range(num_rows)]

        # create a 52 x 52 table that maps each pair of starting hands to their unique ids
        id_mapping_table = [[0 for k in range(52)]for j in range(52)]

        # for each starting pair, calculate average hand strength with 3 faced up community cards for num_simulation
        # times and enter into flop_table

        # for each starting pair, calculate average hand strength with 4 faced up community cards for num_simulation
        # times and enter into turn_table

        # for each starting pair, calculate average hand strength with 5 faced up community cards for num_simulation
        # times and enter into river_table


    def declare_action(self, valid_actions, hole_card, round_state):
        before_action_dt = datetime.datetime.now()
        community_cards = round_state['community_card']
        winrate = self.winrates[hole_card[0][1]][hole_card[1][1]]
        # print(winrate)

        # all features that will be used in q learning
        # current_street = round_state['street']  # current street
        # opp_num_raises = self.opp_num_raises
        # self_num_raises = self.self_raises
        # get hand strength with monte carlo simulation of 100 times
        # hand_str = self.get_hand_strength(hole_card, community_cards, 100)
        # pot_size = round_state['pot']['main']['amount']
        # opp_play_style = self.get_opponent_play_style()
        # get hand potential with monte carlo simulation of 100 x 100 times
        # ppot, npot = self.get_hand_potential(hole_card, community_cards, 30)
        # eff_hand_str = hand_str + (1 - hand_str) * ppot

        # print("current street: " + current_street)
        # print("opp raises: " + str(opp_num_raises))
        # print("self raises: " + str(self_num_raises))
        # print("hand str: " + str(hand_str))
        # print("pot size: " + str(pot_size))
        # print("opp play style: " + opp_play_style)
        # print("ppot: " + str(ppot))
        # print("npot: " + str(npot))
        # print(str(eff_hand_str))

        last_action = len(valid_actions) - 1
        if float(winrate) > self.threshold:
            call_action_info = valid_actions[last_action]
        else:
            call_action_info = valid_actions[0]

        action = call_action_info["action"]
        after_action_dt = datetime.datetime.now()

        # print("Time elapsed in seconds :" + (str)((after_action_dt - before_action_dt).total_seconds()))

        return action

    def action_based_on_hand(self, hole_card, community_cards, valid_actions):
        # print(hole_card[0])
        # print(hole_card[1])
        # call is action[1], fold is action[0], raise is action[2]
        last_action = len(valid_actions) - 1
        if self.has_pair(hole_card, community_cards):
            call_action_info = valid_actions[last_action]  # call the last action (either call or raise)
        elif self.has_mediocre_card(hole_card) or self.has_high_card(hole_card):
            call_action_info = valid_actions[1]  # call when have mediocre hand
        else:
            call_action_info = valid_actions[0]  # fold when hand is weak
        return call_action_info

    def receive_game_start_message(self, game_info):
        for seat in game_info['seats']:
            if seat['uuid'] != self.uuid:
                self.opp_uuid = seat['uuid']
        # print("my uuid: " + self.uuid)
        # print("opp uuid: " + self.opp_uuid)

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.num_rounds_played += 1

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        curr_player_uuid = action['player_uuid']
        # get the number of raises, calls and folds from opponent
        if curr_player_uuid == self.opp_uuid:
            if action['action'] == 'raise':
                self.opp_num_raises += 1
            elif action['action'] == 'call':
                self.opp_num_calls += 1
            else:
                self.opp_num_folds += 1
        else:
            # get self raises
            if action['action'] == 'raise':
                self.self_raises += 1

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def setup_ai():
    return RVPlayer()