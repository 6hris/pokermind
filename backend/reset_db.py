#!/usr/bin/env python
import os
import argparse
import sys

def reset_database(auto_confirm=False):
    """
    Reset the leaderboard database by removing the database file.
    
    Args:
        auto_confirm: If True, skip confirmation prompt
    """
    # Define path to the database file
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'leaderboard.db')
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    # Confirm deletion unless auto mode is enabled
    if not auto_confirm:
        response = input(f"Are you sure you want to delete the leaderboard database at {db_path}? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return
    
    # Delete the database file
    try:
        os.remove(db_path)
        print(f"Database file at {db_path} has been deleted.")
    except Exception as e:
        print(f"Error deleting database file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset the poker leaderboard database.")
    parser.add_argument('--auto', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    reset_database(auto_confirm=args.auto)