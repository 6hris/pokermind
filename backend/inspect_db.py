import sqlite3
import json
from contextlib import contextmanager

@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect('leaderboard.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def display_section(title):
    """Display a section title."""
    print(f"\n{'-' * 70}")
    print(f"  {title}")
    print(f"{'-' * 70}")

def inspect_models():
    """Display all registered models."""
    display_section("Registered Models")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models")
        rows = cursor.fetchall()
        
        if not rows:
            print("No models found in the database.")
            return
            
        for row in rows:
            print(f"ID: {row['id']}, Name: {row['name']}, Description: {row['description']}")

def inspect_games():
    """Display all games."""
    display_section("Games")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT g.*, COUNT(DISTINCT gp.model_id) as player_count
        FROM games g
        LEFT JOIN game_participants gp ON g.id = gp.game_id
        GROUP BY g.id
        ORDER BY g.start_time DESC
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("No games found in the database.")
            return
            
        for row in rows:
            official = "OFFICIAL" if row['is_official'] else "Exhibition"
            print(f"Game ID: {row['id']} ({official})")
            print(f"  Status: {row['status']}")
            print(f"  Started: {row['start_time']}, Ended: {row['end_time'] or 'In progress'}")
            print(f"  Settings: {row['num_hands']} hands, {row['starting_chips']} chips, SB/BB: {row['small_blind']}/{row['big_blind']}")
            print(f"  Player count: {row['player_count']}")
            print()

def inspect_game_participants():
    """Display game participants and their results."""
    display_section("Game Participants")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            g.id as game_id, 
            m.name as model_name, 
            gp.final_chips,
            g.starting_chips,
            (gp.final_chips - g.starting_chips) as profit_loss,
            g.status,
            g.is_official
        FROM game_participants gp
        JOIN games g ON gp.game_id = g.id
        JOIN models m ON gp.model_id = m.id
        ORDER BY g.start_time DESC, profit_loss DESC
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("No game participants found in the database.")
            return
        
        current_game = None
        for row in rows:
            if current_game != row['game_id']:
                current_game = row['game_id']
                official = "OFFICIAL" if row['is_official'] else "Exhibition"
                status = row['status']
                print(f"\nGame: {current_game} ({status}) - {official}")
                
            profit = row['profit_loss'] if row['final_chips'] is not None else "N/A"
            if profit != "N/A":
                profit_str = f"+{profit}" if profit > 0 else str(profit)
            else:
                profit_str = "N/A"
                
            print(f"  {row['model_name']}: {row['final_chips'] or 'In progress'} chips ({profit_str})")

def inspect_hand_results():
    """Display hand-by-hand results."""
    display_section("Hand Results")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            hr.game_id,
            g.is_official,
            hr.hand_number,
            m.name as model_name,
            hr.profit_loss,
            hr.won_hand,
            hr.starting_chips,
            hr.ending_chips
        FROM hand_results hr
        JOIN models m ON hr.model_id = m.id
        JOIN games g ON hr.game_id = g.id
        ORDER BY hr.game_id, hr.hand_number, hr.profit_loss DESC
        LIMIT 100  -- Limit to prevent overwhelming output
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("No hand results found in the database.")
            return
            
        current_game = None
        current_hand = None
        
        for row in rows:
            # Display game header if we're on a new game
            if current_game != row['game_id']:
                current_game = row['game_id']
                current_hand = None
                official = "OFFICIAL" if row['is_official'] else "Exhibition"
                print(f"\nGame: {current_game} ({official})")
                
            # Display hand header if we're on a new hand
            if current_hand != row['hand_number']:
                current_hand = row['hand_number']
                print(f"  Hand #{current_hand}:")
                
            # Display result
            profit = row['profit_loss']
            profit_str = f"+{profit}" if profit > 0 else str(profit)
            result = "WON" if row['won_hand'] else "lost"
            print(f"    {row['model_name']}: {profit_str} chips ({result}) - {row['starting_chips']} → {row['ending_chips']}")

def get_leaderboard_stats():
    """Display leaderboard statistics."""
    display_section("Leaderboard Statistics")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
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
        GROUP BY 
            m.id
        ORDER BY 
            net_profit DESC
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("No leaderboard statistics available.")
            return
            
        print("All Games (Exhibition + Official)")
        print(f"{'Model':<20} {'Games':<8} {'Hands':<8} {'Profit':<10} {'Win Rate':<10} {'BB/100':<10}")
        print("-" * 70)
        
        for row in rows:
            print(f"{row['model_name']:<20} {row['games_played']:<8} {row['hands_played']:<8} {row['net_profit']:<10} {row['win_rate']}%{'':<4} {row['bb_per_100']:<10}")
            
        # Official games only
        print("\nOfficial Games Only")
        cursor.execute("""
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
            g.is_official = 1
        GROUP BY 
            m.id
        ORDER BY 
            net_profit DESC
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("No official game statistics available.")
            return
            
        print(f"{'Model':<20} {'Games':<8} {'Hands':<8} {'Profit':<10} {'Win Rate':<10} {'BB/100':<10}")
        print("-" * 70)
        
        for row in rows:
            print(f"{row['model_name']:<20} {row['games_played']:<8} {row['hands_played']:<8} {row['net_profit']:<10} {row['win_rate']}%{'':<4} {row['bb_per_100']:<10}")

def main():
    """Main function to run the database inspection."""
    print("Inspecting Leaderboard Database")
    
    try:
        # Check if database exists and has tables
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if not tables:
                print("No tables found in the database. It may be empty or not initialized.")
                return
                
            # Display database info
            display_section("Database Information")
            print(f"Database contains {len(tables)} tables:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table['name']}")
                count = cursor.fetchone()[0]
                print(f"  - {table['name']}: {count} rows")
            
        # Run inspection functions
        inspect_models()
        inspect_games()
        inspect_game_participants()
        inspect_hand_results()
        get_leaderboard_stats()
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()