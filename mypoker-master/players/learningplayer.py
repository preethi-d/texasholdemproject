from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.utils.card_utils import _fill_community_card, _pick_unused_card, gen_cards
import random as rand


class LearningPlayer(BasePokerPlayer):
    opp_num_raises = 0
    opp_num_calls = 0
    opp_num_folds = 0
    self_raises = 0
    num_rounds_played = 0

    def __init__(self):
        self.actionHistory = []
        self.gameHistory = []
        self.table = {}
        self.qtable = {}
        self.epsilon = 0.1
        self.learn_factor = 0.02
        self.bb = 0
        self.unseen = 0
        self.num_rounds_this_game = 0
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

    def set_table(self, current_street, ehs, pot_size, opp_play_style, self_raises, action, _reward, num_iter):
        table = self.qtable
        if not current_street in table: table[current_street] = {}
        if not ehs in table[current_street]: table[current_street][ehs] = {}
        if not pot_size in table[current_street][ehs]: table[current_street][ehs][pot_size] = {}
        if not opp_play_style in table[current_street][ehs][pot_size]: table[current_street][ehs][pot_size][ \
            opp_play_style] = {}
        if not self_raises in table[current_street][ehs][pot_size][opp_play_style]:
            table[current_street][ehs][pot_size][opp_play_style][self_raises] = {}
        if not action in table[current_street][ehs][pot_size][opp_play_style][self_raises]:
            table[current_street][ehs][pot_size][opp_play_style][self_raises][action] = [0, 0]
        table[current_street][ehs][pot_size][opp_play_style][self_raises][action] = [round(float(_reward), 3), int(num_iter)]
        pass

    def update_table(self, current_street, _ehs, _pot_size, opp_play_style, self_raises, action, _reward):
        ehs = "{:.2}".format(float(_ehs))
        pot_size = str(_pot_size)
        reward = _reward / self.bb

        table = self.qtable
        if not current_street in table: table[current_street] = {}
        if not ehs in table[current_street]: table[current_street][ehs] = {}
        if not pot_size in table[current_street][ehs]: table[current_street][ehs][pot_size] = {}
        if not opp_play_style in table[current_street][ehs][pot_size]: table[current_street][ehs][pot_size][
            opp_play_style] = {}
        if not self_raises in table[current_street][ehs][pot_size][opp_play_style]:
            table[current_street][ehs][pot_size][opp_play_style][self_raises] = {}
        if not action in table[current_street][ehs][pot_size][opp_play_style][self_raises]:
            table[current_street][ehs][pot_size][opp_play_style][self_raises][action] = [0, 0]
        q, c = table[current_street][ehs][pot_size][opp_play_style][self_raises][action]
        q2 = q * (1 - self.learn_factor) + reward * self.learn_factor
        self.set_table(current_street, ehs, pot_size, opp_play_style, self_raises, action, q2, c + 1)
        # table[current_street][ehs][pot_size][opp_play_style][self_raises][action] = [q2, c + 1]

    def get_normalized_pot(self, pot):
        return round(pot / self.bb)

    def write_table(self, id):
        file = open("q-table-{}.txt".format(id), "w")
        data = "\n".join(self.dump_table())
        file.write(data)
        print("written to q-table-{}.txt".format(id))

    def dump_table(self):
        out = []
        for _street in self.qtable:
            street = self.qtable[_street]
            for _ehs in street:
                ehs = street[_ehs]
                for _pot in ehs:
                    pot = ehs[_pot]
                    for _opp_play_style in pot:
                        opp_play_style = pot[_opp_play_style]
                        for _self_raises in opp_play_style:
                            self_raises = opp_play_style[_self_raises]
                            for _action in self_raises:
                                q = str(self_raises[_action])
                                out.append(", ".join(
                                    [_street, _ehs, _pot, str(_opp_play_style), str(_self_raises), _action, q]))
                                # print(_street, _ehs, _pot, _opp_play_style, _self_raises, _action, q)

        # print("Unseen combinations", self.unseen)
        return out

    def getEHS(self, street, hole_card, community_card):
        score = HandEvaluator.eval_hand(gen_cards(hole_card), gen_cards(community_card))
        # print(score)
        if str(score) in self.table[street]:
            return round(float(self.table[street][str(score)]), 2)
        print("Unseen combination")
        self.unseen += 1
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
        f = open(filename)
        for i in f:
            street, ehs, pot, opp_ps, self_raises, action, q, n = i.strip().split(", ")
            q = q[1:]
            n = n[:-1]
            # print(street, ehs, pot, opp_ps, self_raises, action, q, n)
            self.set_table(street, ehs, pot, opp_ps, self_raises, action, q, n)

    def declare_action(self, valid_actions, hole_card, round_state):
        street = round_state['street']
        community_card = round_state['community_card']
        ehs = self.getEHS(street, hole_card, community_card)
        print("EHS", ehs)
        pot = self.get_normalized_pot(round_state['pot']['main']['amount'])
        opp_playstyle = self.get_opponent_play_style()
        self_raises = self.self_raises
        action = ''
        isRandom = ''
        # if ehs == 0:
        #     # isRandom = ' (random)'
        #     ehs = float(rand.random())
        #     print('ehs', ehs)
        # if ehs > 0.7 and len(valid_actions) == 3:
        #     self.self_raises += 1
        #     action = 'raise'
        # elif ehs > 0.2:
        #     action = 'call'
        # else:
        #     action = 'fold'

        # Use q-table to determine action
        # print(valid_actions[round(rand.random() * (len(valid_actions) - 1))]['action'])
        # action = 'fold'
        if rand.random() < self.epsilon:
            print("random action")
            action = valid_actions[round(rand.random() * (len(valid_actions) - 1))]['action']
        else:
            attrs = list(map(str, [street, ehs, pot, opp_playstyle, self_raises]))
            print("attrs", attrs)
            tmp = self.qtable
            found = True
            for i in attrs:
                if i in tmp:
                    tmp = tmp[i]
                else:
                    found = False
                    print("Unseen state", i, tmp)
            if not found:
                pass
            else:
                print("tmp", tmp)
                choices = [i for i in tmp]
                print("choices", choices)

        action = valid_actions[round(rand.random() * (len(valid_actions) - 1))]['action']
        # if state in qtable:
        #     action = max_action(qtable[state])
        #     if random < epsilon
        #         action = random action
        # return action

        self.actionHistory.append({
            'street': round_state['street'],
            'pot': round_state['pot']['main']['amount'],
            'hole_cards': hole_card,
            'community_cards': community_card,
            'ehs': str(ehs) + isRandom,
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
        # print("my uuid: " + self.uuid)
        # print("opp uuid: " + self.opp_uuid)

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.num_rounds_played += 1
        self.num_rounds_this_game += 1

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
        # dict_keys([
        # 'street',
        # 'pot',
        # 'community_card',
        # 'dealer_btn',
        # 'next_player',
        # 'small_blind_pos',
        # 'big_blind_pos',
        # 'round_count',
        # 'small_blind_amount',
        # 'seats',
        # 'action_histories'])
        # print(i['round_state'].keys())

        # self.actionHistory.append({
        #     'street': round_state['street'],
        #     'pot': round_state['pot']['main']['amount'],
        #     'hole_cards': hole_card,
        #     'community_cards': community_card,
        #     'ehs': str(ehs) + isRandom,
        #     'action': action,
        #     'opp_playstyle': self.get_opponent_play_style(),
        #     'valid_actions': valid_actions
        # })
        won_round = winners[0]['uuid'] == self.uuid
        reward = round_state['pot']['main']['amount'] * (2 * won_round - 1) / 2
        for action in self.actionHistory:
            self.update_table(action['street'], action['ehs'], action['pot'], action['opp_playstyle'],
                              action['self_raises'], action['action'], reward)

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
