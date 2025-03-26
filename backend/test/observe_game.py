
import requests
import asyncio
import websockets
import json

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

def create_game():
    response = requests.post(f"{API_URL}/games", json={
        "small_blind": 5,
        "big_blind": 10,
        "player_stack": 1000,
        "num_hands": 3,
        "llm_players": [
            {"name": "GPT-Alice", "model": "gpt-4"},
            {"name": "GPT-Bob", "model": "gpt-4"},
            {"name": "GPT-Charlie", "model": "gpt-4"}
        ]
    })
    response.raise_for_status()
    return response.json()["game_id"]

def start_game(game_id):
    response = requests.post(f"{API_URL}/games/{game_id}/start")
    response.raise_for_status()
    return response.json()

async def observe_game(game_id):
    uri = f"{WS_URL}/ws/games/{game_id}"
    async with websockets.connect(uri) as websocket:
        print(f"Connected to game {game_id}. Waiting for events...\n")
        while True:
            try:
                message = await websocket.recv()
                event = json.loads(message)
                event_type = event.get("event")
                data = event.get("data")
                print(f"[{event_type.upper()}]\n{json.dumps(data, indent=2)}\n")
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket closed.")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

async def main():
    game_id = create_game()
    print(f"Game created: {game_id}")
    await asyncio.sleep(1)
    asyncio.create_task(observe_game(game_id))
    await asyncio.sleep(1)
    start_game(game_id)

async def main():
    game_id = create_game()
    print(f"Game created: {game_id}")
    await asyncio.sleep(1)

    # Start observing (keep the task handle)
    observer_task = asyncio.create_task(observe_game(game_id))

    # Start the game
    await asyncio.sleep(1)
    start_game(game_id)

    # Wait for observer to finish (e.g. when game completes)
    await observer_task


if __name__ == "__main__":
    asyncio.run(main())
