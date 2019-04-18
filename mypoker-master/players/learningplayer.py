from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.utils.card_utils import _fill_community_card, _pick_unused_card, gen_cards
import random as rand
import qtable


class LearningPlayer(BasePokerPlayer):
    opp_num_raises = 0
    opp_num_calls = 0
    opp_num_folds = 0
    self_raises = 0
    num_rounds_played = 0

    def __init__(self, log_level=0):
        self.actionHistory = []
        self.gameHistory = []
        self.qtable = qtable.QTable()
        self.table = {}
        self.epsilon = 0.1
        self.learn_factor = 0.05
        self.discount_factor = 0.5
        self.bb = 0
        self.unseen_hands = 0
        self.unseen_states = 0
        self.num_rounds_this_game = 0
        self.log_level = log_level
        streets = ['preflop', 'flop', 'turn', 'river']
        for i in streets:
            self.table[i] = {}

        # read table
        files = ["./hs_data/flop_2500000_500.txt", "./hs_data/river_2500000_500.txt", "./hs_data/turn_2500000_500.txt",
                 "./hs_data/preflop_10000.txt"]
        for f in files:
            file = open(f)
            street = file.readline().strip()
            for i in file:
                # print(i.strip().split(" "))
                score, strength = i.strip().split(" ")
                self.table[street][score] = strength

    def get_table(self, attrs):
        return self.qtable.get(attrs)

    def set_table(self, attrs, val):
        self.qtable.set(attrs, val)

    def update_table(self, attrs, reward):
        lf = self.learn_factor
        q0, c0 = self.get_table(attrs)
        if not q0:
            q0, c0 = 0, 0
            lf = 1

        q1 = q0 * (1 - lf) + reward * lf
        c1 = c0 + 1
        self.log("q: {} -> {} (r: {}|{}) n: {} state: {}".format(str(q0), str(q1), str(reward), str(lf), str(c1), attrs), 1)
        self.set_table(attrs, [q1, c1])

    def get_normalized_pot(self, pot):
        return round(0.5 * pot / self.bb)

    def write_table(self, id):
        filename = "q-table-{}.txt".format(id)
        self.qtable.writefile(filename)
        self.log("written to {}".format(filename), 0)

    def dump_table(self):
        return self.qtable.aslist()

    def getEHS(self, street, hole_card, community_card):
        score = HandEvaluator.eval_hand(gen_cards(hole_card), gen_cards(community_card))
        # print(score)
        if str(score) in self.table[street]:
            return round(float(self.table[street][str(score)]), 2)
        # print("Unseen hand")
        self.unseen_hands += 1
        calc_ehs = self.get_hand_strength(hole_card, community_card, 100)
        self.table[street][score] = calc_ehs
        return round(calc_ehs, 2)
        # print(street, hole_card, community_card, score)
        # # print(self.table[street][str(score)])
        # return 0

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

    def get_opponent_play_style(self):
        aggressive_factor = self.opp_num_raises / (self.opp_num_calls + 1)  # to prevent divide by 0
        player_tightness = self.opp_num_folds / self.num_rounds_played

        # return [aggressive_factor, player_tightness]

        if aggressive_factor > 1 and player_tightness < 0.28:
            return 0
        elif aggressive_factor > 1 and player_tightness >= 0.28:
            return 1
        elif aggressive_factor <= 1 and player_tightness < 0.28:
            return 2
        else:
            return 3

    def load_qtable_from_file(self, filename):
        self.qtable.loadfile(filename)

    def log(self, msg, level = 0):
        if (level <= self.log_level):
            print(msg)

    def declare_action(self, valid_actions, hole_card, round_state):
        street = round_state['street']
        community_card = round_state['community_card']
        ehs = self.getEHS(street, hole_card, community_card)
        pot = self.get_normalized_pot(round_state['pot']['main']['amount'])
        opp_playstyle = self.get_opponent_play_style()
        self_raises = self.self_raises
        action = ''

        # Use q-table with epsilon-greedy algo to determine action
        if rand.random() < self.epsilon:
            action = valid_actions[round(rand.random() * (len(valid_actions) - 1))]['action']
            self.log("random action: {}".format(action), 1)
        else:
            found = False
            actions = [
                'fold', 'call', 'raise'
            ]

            actions = list(map(lambda act: [act, self.get_table({
                    'street': street,
                    'ehs': str(round(ehs, 3)),
                    'pot': str(pot),
                    'action': act
                })[0]], actions))

            best = None
            bestVal = float('-inf')
            for c in actions:
                if c[0] and c[1] and float(c[1]) > bestVal:
                    best = c[0]
                    bestVal = float(c[1])
                    found = True

            found = False
            if not found:
                # print("bye")
                self.unseen_states += 1
                action = valid_actions[round(rand.random() * (len(valid_actions) - 1))]['action']
                self.log("random action: {}".format(action), 1)
            else:
                self.log("Best: {}".format(best), 1)
                action = best

        if action == 'raise':
            self.self_raises += 1

        self.actionHistory.append({
            'street': round_state['street'],
            'pot': pot,
            'hole_cards': hole_card,
            'community_cards': community_card,
            'ehs': str(ehs),
            'action': action,
            'opp_playstyle': self.get_opponent_play_style(),
            'valid_actions': valid_actions,
            'self_raises': self.self_raises
        })
        return action  # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
        # print(game_info)
        self.bb = game_info['rule']['small_blind_amount'] * 2
        self.num_rounds_this_game = 0
        for seat in game_info['seats']:
            if seat['uuid'] != self.uuid:
                self.opp_uuid = seat['uuid']

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.num_rounds_played += 1
        self.num_rounds_this_game += 1
        # print("=" * 5 + "Round {}".format(round_count) + "=" * 5)

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

    def receive_round_result_message(self, winners, hand_info, round_state):
        won_round = winners[0]['uuid'] == self.uuid
        reward = self.get_normalized_pot(round_state['pot']['main']['amount'] * (2 * won_round - 1) / 2)
        for i in range(len(self.actionHistory)):
            action = self.actionHistory[i]
            distance = len(self.actionHistory) - i - 1
            self.update_table({
                'street': action['street'],
                'ehs': action['ehs'],
                'pot': action['pot'],
                'opp_ps': action['opp_playstyle'],
                'self_raises': action['self_raises'],
                'action': action['action']
            }, self.discount_factor**distance * reward)

        self.gameHistory.append({
            'action_history': self.actionHistory,
            'result': winners[0],
            'pot': round_state['pot']['main']['amount'],
            'self_stack': round_state['seats'][0],
            'opp_stack': round_state['seats'][1]
        })
        self.self_raises = 0
        self.actionHistory = []
        pass


def setup_ai():
    return LearningPlayer()
