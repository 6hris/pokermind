import requests
import sys
import json

def test_create_game():
    """Test the create game endpoint."""
    game_config = {
        "small_blind": 5,
        "big_blind": 10,
        "player_stack": 1000,
        "num_hands": 10,
        "llm_players": [
            {
                "name": "Alice (GPT-4)",
                "model": "gpt-4"
            },
            {
                "name": "Bob (Claude)",
                "model": "claude-3-opus"
            }
        ],
        "game_speed": "fast",
        "is_official": False
    }
    
    url = "http://localhost:8000/games"
    response = requests.post(url, json=game_config)
    
    if response.status_code == 200:
        print("Game created successfully\!")
        return response.json()["game_id"]
    else:
        print(f"Failed to create game: {response.status_code} {response.text}")
        return None

def test_official_game():
    """Test creating an official game."""
    game_config = {
        "small_blind": 10,
        "big_blind": 20,
        "player_stack": 1000,
        "num_hands": 100,
        "llm_players": [
            {
                "name": "GPT-4",
                "model": "gpt-4"
            },
            {
                "name": "Claude-3-Opus",
                "model": "claude-3-opus"
            },
            {
                "name": "GPT-3.5",
                "model": "gpt-3.5-turbo"
            }
        ],
        "game_speed": "fast"
    }
    
    url = "http://localhost:8000/admin/official-game"
    response = requests.post(url, json=game_config)
    
    if response.status_code == 200:
        print("Official game created successfully\!")
        return response.json()["game_id"]
    else:
        print(f"Failed to create official game: {response.status_code} {response.text}")
        return None

def test_leaderboard():
    """Test the leaderboard endpoint."""
    # Test official leaderboard
    print("\nTesting Official Leaderboard:")
    url = "http://localhost:8000/leaderboard?official_only=true"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Retrieved {len(data['leaderboard'])} entries")
        print(json.dumps(data, indent=2))
    else:
        print(f"Failed to get leaderboard: {response.status_code} {response.text}")
    
    # Test exhibition leaderboard
    print("\nTesting Exhibition Leaderboard:")
    url = "http://localhost:8000/leaderboard?official_only=false"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Retrieved {len(data['leaderboard'])} entries")
        print(json.dumps(data, indent=2))
    else:
        print(f"Failed to get leaderboard: {response.status_code} {response.text}")

def test_model_stats():
    """Test the model stats endpoint."""
    # Replace with an actual model name if needed
    model_name = "gpt-4"
    
    print(f"\nTesting Model Stats for {model_name}:")
    url = f"http://localhost:8000/leaderboard/{model_name}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Failed to get model stats: {response.status_code} {response.text}")

def cleanup_database():
    """Clean up the test database."""
    print("\nNote: In a real deployment, you would have database cleanup here.")

if __name__ == "__main__":
    print("Starting API tests...")
    
    # The real test would involve running these functions in sequence
    # For now, just demonstrate how to use the endpoints
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        game_id = test_create_game()
        official_game_id = test_official_game()
        test_leaderboard()
        test_model_stats()
    else:
        print("This script demonstrates API test cases.")
        print("Run with 'python test_api.py run' to execute the tests (requires running server).")
