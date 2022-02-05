import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List

import GameData
from AbstractRule import AbstractRule
from Agent import Agent
from DiscardRule import DiscardRule
from HintRule import HintRule
from PlayRule import PlayRule
from PlayerGameState import PlayerGameState
from user_constants import ClientAction, DROP_RULE_PROB, MOVE_RULE_UP_PROB, CREATE_NEW_RULE_PROB

RuleTypeDeserializer = {
    1: PlayRule,
    2: HintRule,
    3: DiscardRule,
}


class GeneticAgent(Agent):
    def __init__(self, player_name: str, rules: List[AbstractRule] = None):
        super().__init__(player_name)
        if rules is None:
            rules = []
        self.rules: List[AbstractRule] = rules

    def choose_action(self) -> ClientAction:
        for rule in self.rules:
            action = rule.apply(self.player_game_state)
            if action is not None:
                return action
        return self.random_hint_or_discard()

    def random_hint_or_discard(self) -> ClientAction:
        action = HintRule(5).apply(self.player_game_state)
        if action is not None:
            return action
        else:
            return DiscardRule(6, 0).apply(self.player_game_state)

    def mutate(self):
        self.rules = [rule for rule in self.rules if random.random() > DROP_RULE_PROB]
        for rule in self.rules:
            rule.mutate()
        for rule_index in range(1, len(self.rules)):
            if random.random() < MOVE_RULE_UP_PROB:
                self.rules[rule_index-1], self.rules[rule_index] = self.rules[rule_index], self.rules[rule_index-1]
        if random.random() < CREATE_NEW_RULE_PROB:
            self.rules.insert(random.randint(0, len(self.rules)),
                              RuleTypeDeserializer[random.randint(1, 3)].create_random())

    def crossover(self, new_player_name: str, other):
        cut_index = random.randint(0, min(len(self.rules), len(other.rules)))
        return GeneticAgent.from_json_encoded(new_player_name,
                                              self.to_json_encoded()['rules'][:cut_index] +
                                              other.to_json_encoded()['rules'][cut_index:])

    def to_json_encoded(self):
        return {'name': self.name, 'rules': [rule.to_json_encoded() for rule in self.rules]}

    @staticmethod
    def from_json_encoded(encoded_object: dict):
        return GeneticAgent(encoded_object['name'],
                            [RuleTypeDeserializer[encoded_rule['rule_type']].from_json_encoded(encoded_rule)
                             for encoded_rule in encoded_object['rules']])
