import random
from abc import ABC, abstractmethod
from typing import Optional

from PlayerGameState import PlayerGameState
from user_constants import ClientAction


class AbstractRule(ABC):
    @abstractmethod
    def apply(self, player_game_state: PlayerGameState) -> Optional[ClientAction]:
        pass

    @abstractmethod
    def mutate(self):
        pass

    @abstractmethod
    def to_json_encoded(self):
        pass

    @staticmethod
    @abstractmethod
    def from_json_encoded(encoded_object):
        pass

    @staticmethod
    @abstractmethod
    def create_random():
        pass


def mutate_probability(probability, sigma):
    return min(1, max(0, probability + random.gauss(0, sigma)))
