"""
Poker Engine Test Script
------------------------
This script tests the core functionality of the poker engine.
It includes basic game flow tests, betting logic, and hand evaluation.
"""

import random
from typing import Tuple, List
from deck import Card, Deck, format_cards
from player import Player, PlayerStatus, PlayerAction
from game import Game

def test_setup():
    """Test basic setup of game and players"""
    players = [
        Player("Alice", False, 1000, 0),
        Player("Bob", False, 1000, 1),
        Player("Charlie", False, 1000, 2),
        Player("Dave", False, 1000, 3)
    ]
    
    game = Game(players, 5, 10)
    
    print("=== Game Setup ===")
    print(f"Players: {[p.name for p in game.players]}")
    print(f"Small Blind: {game.sb}")
    print(f"Big Blind: {game.bb}")
    
    return game


def test_positions(game):
    """Test setting player positions"""
    print("\n=== Position Test ===")
    game.set_player_positions()
    
    for player in game.players:
        position = []
        if player.is_dealer:
            position.append("Dealer")
        if player.is_sb:
            position.append("SB")
        if player.is_bb:
            position.append("BB")
        
        print(f"{player.name}: {', '.join(position) if position else 'None'}")
    
    # Rotate positions
    game.rotate_dealer()
    print("\nAfter rotation:")
    
    for player in game.players:
        position = []
        if player.is_dealer:
            position.append("Dealer")
        if player.is_sb:
            position.append("SB")
        if player.is_bb:
            position.append("BB")
        
        print(f"{player.name}: {', '.join(position) if position else 'None'}")


def test_dealing(game):
    """Test dealing cards"""
    print("\n=== Dealing Test ===")
    game.deck.shuffle()
    game.deal_hole_cards()
    
    for player in game.players:
        print(f"{player.name}'s hand: {format_cards(player.hand)}")
    
    print("\nDealing flop:")
    game.deal_community_cards(3)
    print(f"Community cards: {format_cards(game.community_cards)}")
    
    print("\nDealing turn:")
    game.deal_community_cards(1)
    print(f"Community cards: {format_cards(game.community_cards)}")
    
    print("\nDealing river:")
    game.deal_community_cards(1)
    print(f"Community cards: {format_cards(game.community_cards)}")


def test_betting(game):
    """Test betting round"""
    print("\n=== Betting Test ===")
    
    # Reset game state
    game.deck.shuffle()
    for player in game.players:
        player.reset_for_hand()
    game.community_cards = []
    game.pot = 0
    game.current_bet = 0
    
    # Deal cards
    game.deal_hole_cards()
    for player in game.players:
        print(f"{player.name}'s hand: {format_cards(player.hand)}")
    
    # Post blinds
    game.post_blinds()
    print("\nPosting blinds:")
    for player in game.players:
        print(f"{player.name}: Chips={player.chips}, Current Bet={player.current_bet}")
    
    # Pre-flop betting
    print("\nPre-flop betting:")
    game.betting_round("pre-flop")
    print("After pre-flop:")
    for player in game.players:
        status = player.status.value if player.status != PlayerStatus.ACTIVE else "active"
        print(f"{player.name}: Chips={player.chips}, Bet={player.current_bet}, Status={status}")
    print(f"Pot: {game.pot}")
    
    # Deal flop
    if len([p for p in game.players if p.status == PlayerStatus.ACTIVE]) > 1:
        game.deal_community_cards(3)
        print(f"\nFlop: {format_cards(game.community_cards)}")
        
        # Flop betting
        game.betting_round("flop")
        print("After flop betting:")
        for player in game.players:
            status = player.status.value if player.status != PlayerStatus.ACTIVE else "active"
            print(f"{player.name}: Chips={player.chips}, Bet={player.current_bet}, Status={status}")
        print(f"Pot: {game.pot}")


def test_full_hand(game):
    """Test playing a full hand"""
    print("\n=== Full Hand Test ===")
    
    # Reset game state
    for player in game.players:
        player.reset_for_hand()
        player.chips = 1000  # Reset chips for testing
    
    game.play_hand()
    print(f"Community cards: {format_cards(game.community_cards)}")
    
    print("\nAfter hand:")
    for player in game.players:
        print(f"{player.name}: Chips={player.chips}")


def test_hand_evaluation():
    """Test hand evaluation logic"""
    print("\n=== Hand Evaluation Test ===")
    
    # Create specific hands for testing
    # This is basic and should be expanded with more test cases
    deck = Deck()
    
    # Test flush
    flush = [
        Card("hearts", "A"),
        Card("hearts", "5"),
        Card("hearts", "7"),
        Card("hearts", "9"),
        Card("hearts", "J"),
    ]
    
    # Test straight
    straight = [
        Card("hearts", "A"),
        Card("diamonds", "2"),
        Card("clubs", "3"),
        Card("spades", "4"),
        Card("hearts", "5"),
    ]
    
    # Test full house
    full_house = [
        Card("hearts", "K"),
        Card("diamonds", "K"),
        Card("clubs", "K"),
        Card("spades", "5"),
        Card("hearts", "5"),
    ]
    
    # Creating a temporary game just for evaluation
    temp_game = Game([], 5, 10)
    
    # Testing different hands
    for hand, name in [(flush, "Flush"), (straight, "Straight"), (full_house, "Full House")]:
        print(f"Testing {name}: {format_cards(hand)}")
        temp_game.community_cards = hand[2:] # First 3 cards as community
        result = temp_game.evaluate_hand(hand[:2])  # Last 2 as hole cards
        print(f"Evaluation result: {result}")


def main():
    """Main test function"""
    # Run tests
    game = test_setup()
    test_positions(game)
    test_dealing(game)
    test_betting(game)
    test_full_hand(game)
    test_hand_evaluation()


if __name__ == "__main__":
    main()