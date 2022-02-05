import json
import logging
import socket
import sys

from GeneticAgent import GeneticAgent
from SocketAgent import SocketAgent

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    with open('best_agent.json', 'r') as f:
        loaded_gent = GeneticAgent.from_json_encoded(json.load(f))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        agent = SocketAgent(s, loaded_gent)
        agent.play_game()
