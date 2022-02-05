import logging
import select
from typing import get_args, Optional
import socket

from Agent import Agent
import GameData
from constants import HOST, PORT, DATASIZE
from user_constants import ActionPerformed


class SocketAgent:
    def __init__(self, socket: socket, agent: Agent):
        self.socket = socket
        self.agent = agent
        self.score = 0
        self.is_game_running = True

    def join(self) -> bool:
        self.socket.connect((HOST, PORT))
        self.socket.send(GameData.ClientPlayerAddData(self.agent.name).serialize())
        data = self.socket.recv(DATASIZE)
        data = GameData.GameData.deserialize(data)
        if type(data) is GameData.ServerPlayerConnectionOk:
            logging.debug(f"Agent {self.agent.name} connected.")
            return True
        self.handle_unexpected_data(data, f"fUnexpected data received when {self.agent.name} tried to join the game.")
        return False

    def play_game(self):
        self.join()
        self.send_ready()
        current_player = self.wait_for_start()
        self.get_game_state()
        while self.is_game_running:
            logging.debug(f"It's \"{current_player}\"'s turn.")
            if select.select([self.socket], [], [], 2)[0]:
                data = self.socket.recv(DATASIZE)
                if data:
                    data = GameData.GameData.deserialize(data)
                    current_player = self.handle_data_received(data)
                    if current_player is None:
                        return
            print(f"player {self.agent.name}, cur: {current_player}")
            if self.agent.name == current_player:
                logging.debug(f"Player {self.agent.name} is computing his turn")
                self.get_game_state()
                self.socket.send(self.agent.choose_action().serialize())

    def send_ready(self) -> bool:
        self.socket.send(GameData.ClientPlayerStartRequest(self.agent.name).serialize())
        data = self.socket.recv(DATASIZE)
        data = GameData.GameData.deserialize(data)
        if type(data) is GameData.ServerPlayerStartRequestAccepted:
            logging.info(
                f"{self.agent.name} is ready. {data.acceptedStartRequests}/{data.connectedPlayers} players ready.")
            return True
        self.handle_unexpected_data(data, f"Unexpected data received when {self.agent.name} sent ready.")
        return False

    def wait_for_start(self) -> Optional[str]:
        data = GameData.GameData.deserialize(self.socket.recv(DATASIZE))
        if type(data) is GameData.ServerStartGameData:
            self.socket.send(GameData.ClientPlayerReadyData(self.agent.name).serialize())
            logging.info(f"Game has started for {self.agent.name}.")
            return data.players[0]
        self.handle_unexpected_data(data, f"Unexpected data received when {self.agent.name} waited for start.")
        return None

    def get_game_state(self):
        logging.debug(f"Player {self.agent.name} requested a game state update.")
        self.socket.send(GameData.ClientGetGameStateRequest(self.agent.name).serialize())
        data = GameData.GameData.deserialize(self.socket.recv(DATASIZE))
        for player in data.players:
            logging.debug(f"Player {player.name} cards: {[[card.color, card.value] for card in player.hand]}")
        if type(data) is GameData.ServerGameStateData:
            self.agent.update_game_state(data)
            return
        self.handle_unexpected_data(data, "Couldn't get game state")
        return

    def handle_data_received(self, data: GameData.ServerToClientData) -> Optional[str]:
        if isinstance(data, get_args(ActionPerformed)):
            return self.handle_action_performed(data)
        elif type(data) is GameData.ServerGameStateData:
            return self.handle_update_game_state(data)
        elif type(data) is GameData.ServerGameOver:
            self.handle_game_over(data)
            return None
        else:
            self.handle_unexpected_data(data, f"Couldn't identify data.")
            return None

    def handle_update_game_state(self, data: GameData.ServerGameStateData) -> str:
        logging.debug(f"Player {self.agent.name} received a game state update")
        self.agent.update_game_state(data)
        return data.currentPlayer

    def handle_action_performed(self, action: ActionPerformed) -> str:
        if type(action) is GameData.ServerPlayerMoveOk:
            logging.debug(f"Card played")
            self.agent.register_card_play(action)
        elif type(action) is GameData.ServerActionValid:
            logging.debug(f"Card discarded")
        elif type(action) is GameData.ServerHintData:
            logging.debug(f"Hint given")
            self.agent.register_hint(action)
        elif type(action) is GameData.ServerPlayerThunderStrike:
            logging.debug(f"Thunder")
        else:
            self.handle_unexpected_data(action, f"Unexpected action performed.")
        logging.debug(f"It's \"{action.player}\"'s turn")
        return action.player

    def handle_game_over(self, data: GameData.ServerGameOver):
        logging.info(f"Game ended. Score: {data.score}, {data.sender}. {data.message}")
        self.score = data.score
        self.is_game_running = False

    def handle_unexpected_data(self, data: GameData.ServerToClientData, msg: Optional[str] = None):
        if msg is not None:
            logging.warning(msg)
        if type(data) is GameData.ServerInvalidDataReceived:
            logging.warning(f"Invalid data sent. {data.data}")
        elif type(data) is GameData.ServerActionInvalid:
            logging.warning(f"Somebody performed an invalid action. {data.message}")
        else:
            logging.warning(f"Unexpected data type received. {type(data)}")
