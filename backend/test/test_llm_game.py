import os
from player import Player
from llm_player import LLMPlayer
from game import Game
from dotenv import load_dotenv

load_dotenv()

def test_llm_players():
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found! Please check your .env file.")
    
    players = [
        LLMPlayer("GPT-4-Bob", 1000, 0, "gpt-4o", OPENAI_API_KEY),
        LLMPlayer("GPT-4-Ann", 1000, 1, "gpt-4o", OPENAI_API_KEY),
        LLMPlayer("GPT-4-Joe", 1000, 2, "gpt-4o", OPENAI_API_KEY)
    ]

    game = Game(players, sb=5, bb=10)

    print("\n=== Starting Poker Game with LLM Players ===\n")

    num_hands = 2  # number of hands to play for testing purposes
    for i in range(num_hands):
        print(f"\n\n================== HAND {i+1} ==================\n")
        game.play_hand()

    print("\n=== Final Chip Counts ===")
    for player in players:
        print(f"{player.name}: {player.chips} chips")


if __name__ == "__main__":
    test_llm_players()
