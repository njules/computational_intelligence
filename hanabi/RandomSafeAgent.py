from typing import Optional, Union

import GameData
from Agent import GeneticAgent, ClientAction
from PlayerGameState import PlayerGameState, NUM_HINT_TOKENS


class RandomSafeAgent(GeneticAgent):
    def choose_action(self) -> ClientAction:
        if self.player_game_state.hint_tokens < NUM_HINT_TOKENS:
            return GameData.ClientPlayerDiscardCardRequest(self.name, 4)
        else:
            return GameData.ClientHintData(self.name, 'Player2', 'color', 'blue')
