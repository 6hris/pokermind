import os
import asyncio
from player import Player
from llm_player import LLMPlayer
from game import Game
from leaderboard import LeaderboardManager
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def run_test_game():
    """Run a simple test game and record results in the leaderboard."""
    
    # Create a unique game ID
    game_id = str(uuid.uuid4())
    print(f"Creating game with ID: {game_id}")
    
    # Game settings
    num_hands = 5
    starting_chips = 1000
    small_blind = 5
    big_blind = 10
    
    # Initialize players
    players = [
        LLMPlayer("GPT-4-Player", starting_chips, 0, "gpt-4", os.getenv("OPENAI_API_KEY")),
        LLMPlayer("GPT-3.5-Player", starting_chips, 1, "gpt-3.5-turbo", os.getenv("OPENAI_API_KEY"))
    ]
    
    # Initialize leaderboard manager
    leaderboard = LeaderboardManager()
    
    # Register the game in the leaderboard
    model_names = [player.model_name for player in players]
    leaderboard.register_game(
        game_id=game_id,
        starting_chips=starting_chips,
        small_blind=small_blind,
        big_blind=big_blind,
        num_hands=num_hands,
        models=model_names,
        is_official=False
    )
    
    # Set up the game with a simple callback for logging
    async def game_callback(event_type, data):
        print(f"Event: {event_type}")
    
    game = Game(players, sb=small_blind, bb=big_blind, callback=game_callback)
    
    print("\n=== Starting Poker Game with LLM Players ===\n")
    
    # Play the specified number of hands
    for i in range(num_hands):
        print(f"\n\n================== HAND {i+1} ==================\n")
        
        # Store previous chip counts
        prev_chips = {player.name: player.chips for player in players}
        
        # Play the hand (async)
        result = await game.play_hand()
        
        # Get the winners from the hand result
        winners = [player.name for player in result.get('winners', [])] if result and 'winners' in result else []
        
        # Record results for each player
        for player in players:
            profit_loss = player.chips - prev_chips[player.name]
            won_hand = player.name in winners
            
            # Record in leaderboard
            leaderboard.record_hand_result(
                game_id=game_id,
                hand_number=i+1,
                model_name=player.model_name,
                profit_loss=profit_loss,
                won_hand=won_hand,
                starting_chips=prev_chips[player.name],
                ending_chips=player.chips,
                big_blind=big_blind
            )
    
    # Complete the game in the leaderboard
    final_chips = {player.model_name: player.chips for player in players}
    leaderboard.complete_game(game_id, final_chips)
    
    print("\n=== Final Chip Counts ===")
    for player in players:
        print(f"{player.name} ({player.model_name}): {player.chips} chips")
    
    print("\n=== Leaderboard Stats ===")
    stats = leaderboard.get_leaderboard(limit=10, official_only=False)
    for entry in stats:
        print(f"{entry['model_name']}: {entry['net_profit']} chips, {entry['win_rate']}% win rate")

if __name__ == "__main__":
    # Run the async function
    asyncio.run(run_test_game())