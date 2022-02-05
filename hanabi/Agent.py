from abc import ABC, abstractmethod
from typing import Optional, Union
import socket

import GameData
from PlayerGameState import PlayerGameState
from user_constants import ClientAction


class Agent(ABC):
    def __init__(self, player_name):
        self.name = player_name
        self.player_game_state = PlayerGameState(player_name)

    def register_hint(self, hint: GameData.ServerHintData):
        self.player_game_state.register_hint(hint)

    def register_card_play(self, play: GameData.ServerPlayerMoveOk):
        self.player_game_state.register_card_played(play.cardHandIndex)

    def update_game_state(self, game_state: GameData.ServerGameStateData):
        self.player_game_state.update_game_state(game_state)

    @abstractmethod
    def choose_action(self) -> ClientAction:
        pass
