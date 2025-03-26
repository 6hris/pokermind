import os
import asyncio
import uuid
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from game import Game, GameEvent
from player import Player
from llm_player import LLMPlayer
from deck import format_cards

# Load environment variables
load_dotenv()

app = FastAPI(title="PokerMind API")

# Add CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active games
games = {}
connected_clients = {}

class GameConfig(BaseModel):
    small_blind: int = Field(..., gt=0, description="Small blind amount")
    big_blind: int = Field(..., gt=0, description="Big blind amount")
    player_stack: int = Field(..., gt=0, description="Starting chips for each player")
    num_hands: int = Field(..., gt=0, description="Number of hands to play")
    llm_players: List[Dict[str, str]] = Field(..., description="List of LLM players to add to the game")

class GameManager:
    def __init__(self):
        self.active_games = {}
        self.game_tasks = {}
    
    def create_game(self, config: GameConfig) -> str:
        """Create a new game with the provided configuration"""
        game_id = str(uuid.uuid4())
        
        # Create players list with LLM players
        players = []
        for i, llm_config in enumerate(config.llm_players):
            player = LLMPlayer(
                name=llm_config["name"],
                chips=config.player_stack,
                position=i,
                model_name=llm_config["model"],
                api_key=os.getenv("OPENAI_API_KEY")  # Get API key from environment
            )
            players.append(player)
        
        # Create the game instance
        async def game_callback(event_type: str, data: Dict[str, Any]):
            """Callback function to broadcast game events to connected clients"""
            if game_id in connected_clients:
                event_data = {
                    "event": event_type,
                    "data": data
                }
                for client in connected_clients[game_id]:
                    await client.send_json(event_data)
        
        game = Game(
            players=players,
            sb=config.small_blind,
            bb=config.big_blind,
            callback=game_callback
        )
        
        # Store game and configuration
        self.active_games[game_id] = {
            "game": game,
            "config": config,
            "status": "created"
        }
        
        return game_id
    
    async def start_game(self, game_id: str):
        """Start a game that has been created"""
        if game_id not in self.active_games:
            raise ValueError(f"Game {game_id} not found")
        
        game_info = self.active_games[game_id]
        game = game_info["game"]
        config = game_info["config"]
        
        # Update game status
        game_info["status"] = "running"
        
        # Start the game in a separate task
        task = asyncio.create_task(game.play_game(config.num_hands))
        self.game_tasks[game_id] = task
        
        # Wait for game to complete
        try:
            await task
            game_info["status"] = "completed"
        except Exception as e:
            game_info["status"] = "error"
            game_info["error"] = str(e)
            raise e
    
    def get_game_state(self, game_id: str) -> Dict[str, Any]:
        """Get the current state of a game"""
        if game_id not in self.active_games:
            raise ValueError(f"Game {game_id} not found")
        
        game_info = self.active_games[game_id]
        game = game_info["game"]
        
        return {
            "game_id": game_id,
            "status": game_info["status"],
            "current_stage": game.current_stage.value if hasattr(game, "current_stage") else None,
            "hand_number": game.hand_number,
            "pot": game.pot,
            "community_cards": format_cards(game.community_cards) if game.community_cards else "",
            "players": [
                {
                    "name": player.name,
                    "chips": player.chips,
                    "status": player.status.value,
                    "position": player.position,
                    "is_dealer": player.is_dealer,
                    "is_sb": player.is_sb,
                    "is_bb": player.is_bb
                }
                for player in game.players
            ]
        }

# Create game manager
game_manager = GameManager()

@app.post("/games")
async def create_game(config: GameConfig):
    """Create a new poker game"""
    try:
        game_id = game_manager.create_game(config)
        return {"game_id": game_id, "message": "Game created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/games/{game_id}/start")
async def start_game(game_id: str):
    """Start a created game"""
    try:
        # Start the game asynchronously (don't wait for it to complete)
        asyncio.create_task(game_manager.start_game(game_id))
        return {"message": f"Game {game_id} started"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/games/{game_id}")
async def get_game(game_id: str):
    """Get the current state of a game"""
    try:
        game_state = game_manager.get_game_state(game_id)
        return game_state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/games/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """WebSocket endpoint for real-time game updates"""
    await websocket.accept()
    
    # Register client
    if game_id not in connected_clients:
        connected_clients[game_id] = []
    connected_clients[game_id].append(websocket)
    
    try:
        # Send current game state immediately after connection
        try:
            game_state = game_manager.get_game_state(game_id)
            await websocket.send_json({
                "event": "game_state", 
                "data": game_state
            })
        except ValueError:
            await websocket.send_json({
                "event": "error",
                "data": {"message": f"Game {game_id} not found"}
            })
        
        # Keep connection open to receive updates
        while True:
            # Just wait for client message or disconnection
            data = await websocket.receive_text()
            # Echo back any messages (not really needed for this application)
            await websocket.send_json({"event": "echo", "data": data})
    except WebSocketDisconnect:
        # Remove client on disconnect
        if game_id in connected_clients and websocket in connected_clients[game_id]:
            connected_clients[game_id].remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)