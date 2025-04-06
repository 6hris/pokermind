import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

class LeaderboardManager:
    """Manages the leaderboard data for LLM poker performances."""
    
    # Class-level connection to avoid multiple connections
    _conn = None
    
    def __init__(self, db_path="leaderboard.db"):
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Create the database tables if they don't exist."""
        # Create a new connection only if we don't have one
        if LeaderboardManager._conn is None:
            LeaderboardManager._conn = sqlite3.connect(self.db_path, timeout=60.0, check_same_thread=False)
            LeaderboardManager._conn.execute("PRAGMA busy_timeout = 60000")  # 60 seconds timeout
        
        cursor = LeaderboardManager._conn.cursor()
        
        # Create models table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
        ''')
        
        # Create games table with official flag
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            starting_chips INTEGER NOT NULL,
            small_blind INTEGER NOT NULL,
            big_blind INTEGER NOT NULL,
            num_hands INTEGER NOT NULL,
            status TEXT NOT NULL,
            is_official BOOLEAN NOT NULL DEFAULT 0
        )
        ''')
        
        # Create game_participants table to track which models played in each game
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            model_id INTEGER NOT NULL,
            final_chips INTEGER,
            FOREIGN KEY (game_id) REFERENCES games (id),
            FOREIGN KEY (model_id) REFERENCES models (id)
        )
        ''')
        
        # Create hand_results table to track individual hand results
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS hand_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            hand_number INTEGER NOT NULL,
            model_id INTEGER NOT NULL,
            profit_loss INTEGER NOT NULL,
            won_hand BOOLEAN NOT NULL,
            starting_chips INTEGER NOT NULL,
            ending_chips INTEGER NOT NULL,
            big_blind INTEGER NOT NULL,
            FOREIGN KEY (game_id) REFERENCES games (id),
            FOREIGN KEY (model_id) REFERENCES models (id)
        )
        ''')
        
        LeaderboardManager._conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        # If we don't have a connection, create one
        if LeaderboardManager._conn is None:
            LeaderboardManager._conn = sqlite3.connect(self.db_path, timeout=60.0, check_same_thread=False)
            LeaderboardManager._conn.execute("PRAGMA busy_timeout = 60000")
        
        try:
            yield LeaderboardManager._conn
        except sqlite3.OperationalError as e:
            # If we get a database locked error, close and reopen the connection
            if "database is locked" in str(e):
                print("Database lock detected, recreating connection...")
                try:
                    LeaderboardManager._conn.close()
                except:
                    pass
                LeaderboardManager._conn = sqlite3.connect(self.db_path, timeout=60.0, check_same_thread=False)
                LeaderboardManager._conn.execute("PRAGMA busy_timeout = 60000")
                # Retry the operation with new connection
                yield LeaderboardManager._conn
            else:
                raise
    
    def register_model(self, name: str, description: Optional[str] = None) -> int:
        """Register a new model in the leaderboard or get existing model id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if model already exists
            cursor.execute("SELECT id FROM models WHERE name = ?", (name,))
            existing = cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # Insert new model
            cursor.execute(
                "INSERT INTO models (name, description) VALUES (?, ?)",
                (name, description)
            )
            conn.commit()
            return cursor.lastrowid
    
    def register_game(self, game_id: str, starting_chips: int, small_blind: int, 
                      big_blind: int, num_hands: int, models: List[str], is_official: bool = False) -> None:
        """Register a new game and its participants."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert game record
            cursor.execute(
                "INSERT INTO games (id, starting_chips, small_blind, big_blind, num_hands, status, is_official) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (game_id, starting_chips, small_blind, big_blind, num_hands, "in_progress", int(is_official))
            )
            
            # Register and link model participants
            for model_name in models:
                model_id = self.register_model(model_name)
                cursor.execute(
                    "INSERT INTO game_participants (game_id, model_id) VALUES (?, ?)",
                    (game_id, model_id)
                )
            
            conn.commit()
    
    def record_hand_result(self, game_id: str, hand_number: int, 
                          model_name: str, profit_loss: int, won_hand: bool,
                          starting_chips: int, ending_chips: int, big_blind: int) -> None:
        """Record the result of a hand for a specific model."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get model_id
            cursor.execute("SELECT id FROM models WHERE name = ?", (model_name,))
            model_result = cursor.fetchone()
            if not model_result:
                model_id = self.register_model(model_name)
            else:
                model_id = model_result[0]
            
            # Insert hand result
            cursor.execute(
                """INSERT INTO hand_results 
                   (game_id, hand_number, model_id, profit_loss, won_hand, 
                    starting_chips, ending_chips, big_blind) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (game_id, hand_number, model_id, profit_loss, won_hand, 
                 starting_chips, ending_chips, big_blind)
            )
            
            conn.commit()
    
    def complete_game(self, game_id: str, final_chips: Dict[str, int]) -> None:
        """Mark a game as completed and record final chip counts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Update game status
            cursor.execute(
                "UPDATE games SET status = ?, end_time = CURRENT_TIMESTAMP WHERE id = ?",
                ("completed", game_id)
            )
            
            # Update final chip counts for participants
            for model_name, chips in final_chips.items():
                # Get model_id
                cursor.execute("SELECT id FROM models WHERE name = ?", (model_name,))
                model_result = cursor.fetchone()
                if model_result:
                    model_id = model_result[0]
                    
                    # Update participant record
                    cursor.execute(
                        "UPDATE game_participants SET final_chips = ? WHERE game_id = ? AND model_id = ?",
                        (chips, game_id, model_id)
                    )
            
            conn.commit()
    
    def get_leaderboard(self, limit: int = 10, official_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get the current leaderboard based on:
        - Total Net Winnings/Losses
        - Big Blinds per 100 Hands (BB/100)
        - Win Rate (%)
        
        Args:
            limit: Maximum number of results to return
            official_only: If True, only includes results from official games
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT 
                m.name AS model_name,
                COUNT(DISTINCT hr.game_id) AS games_played,
                COUNT(hr.id) AS hands_played,
                SUM(hr.profit_loss) AS net_profit,
                SUM(CASE WHEN hr.won_hand = 1 THEN 1 ELSE 0 END) AS hands_won,
                ROUND(SUM(CASE WHEN hr.won_hand = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(hr.id), 2) AS win_rate,
                ROUND(SUM(hr.profit_loss) * 100.0 / SUM(hr.big_blind) / COUNT(hr.id), 2) AS bb_per_100
            FROM 
                models m
            JOIN 
                hand_results hr ON m.id = hr.model_id
            JOIN
                games g ON hr.game_id = g.id
            WHERE
                {}
            GROUP BY 
                m.id
            ORDER BY 
                net_profit DESC
            LIMIT ?
            """.format("g.is_official = 1" if official_only else "1=1")
            
            cursor.execute(query, (limit,))
            results = []
            
            for row in cursor.fetchall():
                results.append({
                    "model_name": row[0],
                    "games_played": row[1],
                    "hands_played": row[2],
                    "net_profit": row[3],
                    "hands_won": row[4],
                    "win_rate": row[5],  # as percentage
                    "bb_per_100": row[6]  # BB/100 hands
                })
            
            return results
    
    def get_all_games(self, limit: int = 50, include_in_progress: bool = False) -> List[Dict[str, Any]]:
        """Get a list of all games with their details."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            status_filter = "" if include_in_progress else "WHERE g.status = 'completed'"
            
            query = f"""
            SELECT 
                g.id,
                g.start_time,
                g.end_time,
                g.starting_chips,
                g.small_blind,
                g.big_blind,
                g.num_hands,
                g.status,
                g.is_official,
                COUNT(DISTINCT gp.model_id) as num_models,
                GROUP_CONCAT(m.name, ', ') as models
            FROM 
                games g
            JOIN 
                game_participants gp ON g.id = gp.game_id
            JOIN
                models m ON gp.model_id = m.id
            {status_filter}
            GROUP BY
                g.id
            ORDER BY 
                g.start_time DESC
            LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            results = []
            
            for row in cursor.fetchall():
                results.append({
                    "game_id": row[0],
                    "start_time": row[1],
                    "end_time": row[2],
                    "starting_chips": row[3],
                    "small_blind": row[4],
                    "big_blind": row[5],
                    "num_hands": row[6],
                    "status": row[7],
                    "is_official": bool(row[8]),
                    "num_models": row[9],
                    "models": row[10].split(', ') if row[10] else []
                })
            
            return results
            
    def get_model_stats(self, model_name: str, official_only: bool = True) -> Dict[str, Any]:
        """
        Get detailed stats for a specific model.
        
        Args:
            model_name: Name of the model to get stats for
            official_only: If True, only includes results from official games
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get model id
            cursor.execute("SELECT id FROM models WHERE name = ?", (model_name,))
            model_result = cursor.fetchone()
            if not model_result:
                return {"error": f"Model '{model_name}' not found"}
                
            model_id = model_result[0]
            
            # Get overall stats
            query = """
            SELECT 
                COUNT(DISTINCT hr.game_id) AS games_played,
                COUNT(hr.id) AS hands_played,
                SUM(hr.profit_loss) AS net_profit,
                SUM(CASE WHEN hr.won_hand = 1 THEN 1 ELSE 0 END) AS hands_won,
                ROUND(SUM(CASE WHEN hr.won_hand = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(hr.id), 2) AS win_rate,
                ROUND(SUM(hr.profit_loss) * 100.0 / SUM(hr.big_blind) / COUNT(hr.id), 2) AS bb_per_100
            FROM 
                hand_results hr
            JOIN
                games g ON hr.game_id = g.id
            WHERE 
                hr.model_id = ? AND {}
            """.format("g.is_official = 1" if official_only else "1=1")
            
            cursor.execute(query, (model_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"error": f"No data found for model '{model_name}'"}
                
            stats = {
                "model_name": model_name,
                "games_played": row[0],
                "hands_played": row[1],
                "net_profit": row[2],
                "hands_won": row[3],
                "win_rate": row[4],  # as percentage
                "bb_per_100": row[5]  # BB/100 hands
            }
            
            # Get official status counts
            status_query = """
            SELECT 
                g.is_official,
                COUNT(DISTINCT g.id) as game_count,
                COUNT(hr.id) as hand_count,
                SUM(hr.profit_loss) as total_profit
            FROM 
                hand_results hr
            JOIN
                games g ON hr.game_id = g.id
            WHERE
                hr.model_id = ?
            GROUP BY
                g.is_official
            """
            
            cursor.execute(status_query, (model_id,))
            status_counts = {}
            for row in cursor.fetchall():
                status_type = "official" if row[0] == 1 else "exhibition"
                status_counts[status_type] = {
                    "games_played": row[1],
                    "hands_played": row[2],
                    "net_profit": row[3]
                }
            
            stats["status_counts"] = status_counts
            
            # Get recent games
            recent_games_query = """
            SELECT 
                g.id,
                g.start_time,
                g.end_time,
                gp.final_chips,
                g.starting_chips,
                (gp.final_chips - g.starting_chips) AS profit_loss,
                g.is_official
            FROM 
                games g
            JOIN 
                game_participants gp ON g.id = gp.game_id
            WHERE 
                gp.model_id = ? AND g.status = 'completed'
                AND {}
            ORDER BY 
                g.end_time DESC
            LIMIT 5
            """.format("g.is_official = 1" if official_only else "1=1")
            
            cursor.execute(recent_games_query, (model_id,))
            recent_games = []
            
            for row in cursor.fetchall():
                recent_games.append({
                    "game_id": row[0],
                    "start_time": row[1],
                    "end_time": row[2],
                    "final_chips": row[3],
                    "starting_chips": row[4],
                    "profit_loss": row[5],
                    "is_official": bool(row[6])
                })
            
            stats["recent_games"] = recent_games
            return stats