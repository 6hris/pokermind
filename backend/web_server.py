import os
import asyncio
import uuid
from typing import Dict, List, Any, Optional, ClassVar
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from game import Game, GameEvent
from player import Player
from llm_player import LLMPlayer
from deck import format_cards
from leaderboard import LeaderboardManager

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

# Initialize leaderboard manager
leaderboard_manager = LeaderboardManager()

class GameConfig(BaseModel):
    small_blind: int = Field(..., gt=0, description="Small blind amount")
    big_blind: int = Field(..., gt=0, description="Big blind amount")
    player_stack: int = Field(..., gt=0, description="Starting chips for each player")
    num_hands: int = Field(..., gt=0, description="Number of hands to play")
    llm_players: List[Dict[str, str]] = Field(..., description="List of LLM players to add to the game")
    game_speed: str = Field(default="medium", description="Game speed: fast, medium, slow")
    is_official: bool = Field(default=False, description="Whether this game's results should count towards the official leaderboard")
    
    # Game speed presets (in seconds) - using ClassVar to indicate this is not a field
    speed_presets: ClassVar[Dict[str, Dict[str, float]]] = {
        "fast": {"action": 0.5, "stage": 1.0, "hand": 1.5},
        "medium": {"action": 1.5, "stage": 2.5, "hand": 4.0},  
        "slow": {"action": 3.0, "stage": 5.0, "hand": 7.0}
    }

class GameManager:
    def __init__(self):
        self.active_games = {}
        self.game_tasks = {}
        self.player_chips_history = {}  # Track chips for each player after each hand
    
    def create_game(self, config: GameConfig) -> str:
        """Create a new game with the provided configuration"""
        game_id = str(uuid.uuid4())
        
        # Create players list with LLM players
        players = []
        model_names = []
        for i, llm_config in enumerate(config.llm_players):
            # Determine the correct API key based on model
            model_name = llm_config["model"]
            api_key = None
            
            # Anthropic models
            if model_name.startswith("claude"):
                api_key = os.getenv("ANTHROPIC_API_KEY")
            # OpenAI models
            elif model_name.startswith("gpt"):
                api_key = os.getenv("OPENAI_API_KEY")
            # Gemini models
            elif model_name == "gemini-2.0-flash":
                api_key = os.getenv("GEMINI_API_KEY")
                model_name = "gemini/gemini-2.0-flash"
            # O1 models
            elif model_name == "o1-mini":
                api_key = os.getenv("OPENAI_API_KEY")
            # DeepSeek models
            elif model_name == "deepseek-chat":
                api_key = os.getenv("DEEPSEEK_API_KEY")
                model_name = "deepseek/deepseek-chat"
            elif model_name == "deepseek-reasoner":
                api_key = os.getenv("DEEPSEEK_API_KEY")
                model_name = "deepseek/deepseek-reasoner"
            # Add other providers as needed
            else:
                # Default to OpenAI for unknown models
                api_key = os.getenv("OPENAI_API_KEY")
                
            if not api_key:
                raise ValueError(f"No API key found for model {model_name}")
                
            player = LLMPlayer(
                name=llm_config["name"],
                chips=config.player_stack,
                position=i,
                model_name=model_name,
                api_key=api_key
            )
            players.append(player)
            model_names.append(llm_config["model"])
        
        # Initialize chips history
        self.player_chips_history[game_id] = {
            player.name: [config.player_stack] for player in players
        }
        
        # Register game in leaderboard
        leaderboard_manager.register_game(
            game_id=game_id,
            starting_chips=config.player_stack,
            small_blind=config.small_blind,
            big_blind=config.big_blind,
            num_hands=config.num_hands,
            models=model_names,
            is_official=config.is_official
        )
        
        # Create the game instance with extended callback for leaderboard tracking
        async def game_callback(event_type: str, data: Dict[str, Any]):
            """Callback function to broadcast game events and track leaderboard data"""
            # Broadcast to clients
            if game_id in connected_clients:
                event_data = {
                    "event": event_type,
                    "data": data
                }
                for client in connected_clients[game_id]:
                    await client.send_json(event_data)
            
            # Track game data for leaderboard
            game = self.active_games[game_id]["game"]
            
            # Track hand completions for leaderboard
            if event_type == GameEvent.HAND_COMPLETE.value:
                hand_number = game.hand_number
                
                # Get winners from the hand result
                winners = data.get("winners", [])
                winner_names = [winner["name"] for winner in winners]
                is_split_pot = data.get("is_split_pot", False)
                
                # Process each player's results
                for player in game.players:
                    # Store current chips in history
                    self.player_chips_history[game_id][player.name].append(player.chips)
                    
                    # Calculate profit/loss from this hand
                    if len(self.player_chips_history[game_id][player.name]) >= 2:
                        prev_chips = self.player_chips_history[game_id][player.name][-2]
                        current_chips = player.chips
                        profit_loss = current_chips - prev_chips
                        
                        # Check if player won this hand (including split pot)
                        won_hand = player.name in winner_names
                        
                        # Only record for LLM players
                        if isinstance(player, LLMPlayer):
                            leaderboard_manager.record_hand_result(
                                game_id=game_id,
                                hand_number=hand_number,
                                model_name=player.model_name,
                                profit_loss=profit_loss,
                                won_hand=won_hand,
                                starting_chips=prev_chips,
                                ending_chips=current_chips,
                                big_blind=game.bb
                            )
            
            # When game is complete, update final stats
            elif event_type == GameEvent.GAME_COMPLETE.value:
                final_chips = {}
                for player in game.players:
                    if isinstance(player, LLMPlayer):
                        final_chips[player.model_name] = player.chips
                
                leaderboard_manager.complete_game(game_id, final_chips)
        
        # Get game speed parameters
        speed = config.game_speed.lower()
        if speed not in config.speed_presets:
            speed = "medium"  # Default to medium if invalid
        
        speed_params = config.speed_presets[speed]
        
        game = Game(
            players=players,
            sb=config.small_blind,
            bb=config.big_blind,
            callback=game_callback,
            delay_between_actions=speed_params["action"],
            delay_between_stages=speed_params["stage"],
            delay_after_hand=speed_params["hand"]
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
    # Force user-created games to be exhibition games by default
    if not config.is_official:
        pass  # Already set to false, no need to override
    else:
        # For security, you might want to require an admin token here in the future
        # For now, we'll just let the is_official flag pass through
        pass

    try:
        game_id = game_manager.create_game(config)
        return {
            "game_id": game_id, 
            "message": "Game created successfully",
            "is_official": config.is_official
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/admin/official-game")
async def create_official_game(config: GameConfig):
    """
    Create an official game for leaderboard rankings (admin only)
    In a production environment, this would be protected by authentication
    """
    # Force this to be an official game
    config.is_official = True
    
    # Additional validation for official games
    if config.num_hands < 100:
        raise HTTPException(status_code=400, detail="Official games must have at least 100 hands")
    
    # Implement additional authorization checks here
    # In a real system, you would validate an admin token
    
    try:
        game_id = game_manager.create_game(config)
        return {
            "game_id": game_id, 
            "message": "Official game created successfully",
            "is_official": True
        }
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

# Leaderboard API endpoints
@app.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100, description="Number of entries to return"),
    official_only: bool = Query(True, description="Whether to only include official games")
):
    """Get the current leaderboard rankings"""
    try:
        leaderboard = leaderboard_manager.get_leaderboard(limit=limit, official_only=official_only)
        return {
            "leaderboard": leaderboard,
            "is_official": official_only
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leaderboard/{model_name}")
async def get_model_stats(
    model_name: str,
    official_only: bool = Query(True, description="Whether to only include official games")
):
    """Get detailed statistics for a specific model"""
    try:
        stats = leaderboard_manager.get_model_stats(model_name, official_only=official_only)
        if "error" in stats:
            raise HTTPException(status_code=404, detail=stats["error"])
        stats["is_official"] = official_only
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leaderboard/compare")
async def compare_models(
    model_names: List[str] = Query(None, description="List of model names to compare"),
    official_only: bool = Query(True, description="Whether to only include official games")
):
    """Compare statistics between multiple models"""
    if not model_names or len(model_names) < 2:
        raise HTTPException(status_code=400, detail="At least two model names must be provided")
    
    try:
        results = []
        for model_name in model_names:
            stats = leaderboard_manager.get_model_stats(model_name, official_only=official_only)
            if "error" not in stats:
                results.append(stats)
        
        if not results:
            raise HTTPException(status_code=404, detail="No valid models found for comparison")
        
        return {
            "comparison": results,
            "is_official": official_only
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/games")
async def get_all_games(
    limit: int = Query(50, ge=1, le=200, description="Number of games to return"),
    include_in_progress: bool = Query(False, description="Whether to include in-progress games")
):
    """Get a list of all games (admin endpoint)"""
    try:
        games = leaderboard_manager.get_all_games(
            limit=limit, 
            include_in_progress=include_in_progress
        )
        return {"games": games}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)