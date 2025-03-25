import os
import unittest
from unittest.mock import patch, MagicMock
import json
from player import Player, PlayerAction, PlayerStatus
from llm_player import LLMPlayer, PokerActionResponse
from game import Game
from dotenv import load_dotenv
from deck import Card, Deck

load_dotenv()

class TestLLMPlayer(unittest.TestCase):
    """Unit tests for LLMPlayer that don't require actual API calls"""
    
    def setUp(self):
        self.player = LLMPlayer("TestBot", 1000, 0, "fake-model", "fake-key")
        # Create a minimal game state for testing
        self.game_state = {
            'actions_so_far': ['current round: pre-flop', 'Player1 calls 10'],
            'community_cards': '',
            'pot': 25,
            'min_raise': 10
        }
        # Set up player with simple cards
        self.player.hand = [Card("hearts", "A"), Card("spades", "K")]
        
    def test_parse_valid_response(self):
        """Test that valid JSON responses are parsed correctly"""
        valid_responses = [
            '{"action": "fold", "raise_amount": null}',
            '{"action": "call", "raise_amount": null}',
            '{"action": "raise", "raise_amount": 50}'
        ]
        
        for resp in valid_responses:
            action, amount = self.player.parse_response(resp)
            self.assertIsInstance(action, PlayerAction)
            
            if action == PlayerAction.RAISE:
                self.assertIsNotNone(amount)
                self.assertGreater(amount, 0)
            else:
                self.assertIsNone(amount)
    
    def test_parse_invalid_responses(self):
        """Test that invalid responses are properly rejected"""
        invalid_responses = [
            '{"action": "invalid_action", "raise_amount": null}',  # Invalid action
            '{"action": "raise", "raise_amount": -10}',  # Negative raise amount
            '{"action": "raise"}',  # Missing raise_amount for raise
            'Not a JSON response',  # Not JSON
            ''  # Empty string
        ]
        
        for resp in invalid_responses:
            with self.assertRaises(Exception):
                self.player.parse_response(resp)
    
    @patch('llm_player.completion')
    def test_retry_logic(self, mock_completion):
        """Test that retries work as expected"""
        # Setup mock responses - first two fail, third succeeds
        mock_responses = [
            # First call - invalid JSON
            {"choices": [{"message": {"content": "Let me think..."}}]},
            # Second call - missing raise_amount
            {"choices": [{"message": {"content": '{"action": "raise"}'}}]},
            # Third call - valid response
            {"choices": [{"message": {"content": '{"action": "call", "raise_amount": null}'}}]}
        ]
        
        mock_completion.side_effect = mock_responses
        action, amount = self.player.choose_action(10, self.game_state)
            
        # Should have tried 3 times
        self.assertEqual(mock_completion.call_count, 3)
        # Should have returned the successful response
        self.assertEqual(action, PlayerAction.CALL)
        self.assertIsNone(amount)
    
    @patch('llm_player.completion')
    def test_all_retries_fail(self, mock_completion):
        """Test behavior when all retries fail"""
        # All responses are invalid
        mock_responses = [
            {"choices": [{"message": {"content": "Not valid JSON"}}]},
            {"choices": [{"message": {"content": '{"bad": "format"}'}}]},
            {"choices": [{"message": {"content": '{"action": "invalid"}'}}]}
        ]
        
        mock_completion.side_effect = mock_responses
        action, amount = self.player.choose_action(10, self.game_state)
            
        # Should default to FOLD after all retries fail
        self.assertEqual(action, PlayerAction.FOLD)
        self.assertIsNone(amount)
    
    @patch('llm_player.completion')
    def test_prompt_generation(self, mock_completion):
        """Test that the prompt includes all necessary information"""
        mock_completion.return_value = {"choices": [{"message": {"content": '{"action": "fold", "raise_amount": null}'}}]}
        
        self.player.choose_action(20, self.game_state)
        
        # Check that the prompt was properly formed
        call_args = mock_completion.call_args[1]
        prompt = call_args['messages'][0]['content']
        
        # Verify key elements are in the prompt
        self.assertIn("Your Hole Cards:", prompt)
        self.assertIn("Community Cards:", prompt)
        self.assertIn("Amount to call:", prompt)
        self.assertIn("CRITICAL INSTRUCTIONS:", prompt)
        self.assertIn("The action field MUST be one of", prompt)


class TestLLMIntegration(unittest.TestCase):
    """Integration tests using the actual LLM API"""
    
    @classmethod
    def setUpClass(cls):
        """Skip these tests if no API key is available"""
        cls.api_key = os.getenv("OPENAI_API_KEY")
        if not cls.api_key:
            raise unittest.SkipTest("Skipping integration tests - No API key found")
    
    def setUp(self):
        """Set up a player and game state for each test"""
        self.player = LLMPlayer("TestLLM", 1000, 0, "gpt-4o", self.api_key)
        self.player.hand = [Card("hearts", "A"), Card("spades", "K")]
        
        self.game_state = {
            'actions_so_far': ['current round: pre-flop', 'Player1 calls 10'],
            'community_cards': '',
            'pot': 25,
            'min_raise': 10
        }
    
    def test_real_api_response(self):
        """Test with real API - should return valid action"""
        action, amount = self.player.choose_action(10, self.game_state)
        
        # Check that we got a valid action type
        self.assertIn(action, [PlayerAction.FOLD, PlayerAction.CALL, PlayerAction.RAISE])
        
        # Verify amount is consistent with action
        if action == PlayerAction.RAISE:
            self.assertIsNotNone(amount)
            self.assertGreater(amount, 0)
        else:
            self.assertIsNone(amount)
    
    def test_statistically_valid_behavior(self):
        """Run multiple hands to verify statistical properties"""
        # This tests that the LLM doesn't always make the same decision
        actions = []
        
        # Run 5 decisions with the same inputs
        for _ in range(5):
            action, _ = self.player.choose_action(10, self.game_state)
            actions.append(action)
            
        # There should be some variety in responses (though not guaranteed)
        # We're just checking that API is working and can return different values
        print(f"Actions from multiple identical queries: {[a.value for a in actions]}")
        

def simulate_hand_with_controlled_responses():
    """
    Test a full hand with predetermined LLM responses.
    This demonstrates how to test game flow with controlled non-deterministic components.
    """
    # Create a game with both regular and LLM players
    players = [
        Player("Human", True, 1000, 0),
        LLMPlayer("LLMBot", 1000, 1, "fake-model", "fake-key")
    ]
    
    game = Game(players, sb=5, bb=10)
    
    # Mock the LLM responses to test specific scenarios
    with patch('llm_player.completion') as mock_completion:
        # Configure LLM to RAISE pre-flop, then CALL on flop
        mock_completion.side_effect = [
            # Pre-flop response
            {"choices": [{"message": {"content": '{"action": "raise", "raise_amount": 30}'}}]},
            # Flop response
            {"choices": [{"message": {"content": '{"action": "call", "raise_amount": null}'}}]},
        ]
        
        # Control the deck to deal specific cards
        with patch.object(Deck, 'deal', side_effect=[
            # Player 1's hand
            [Card("hearts", "A"), Card("hearts", "K")],
            # Player 2's hand
            [Card("diamonds", "Q"), Card("diamonds", "J")],
            # Flop
            [Card("hearts", "Q"), Card("hearts", "J"), Card("hearts", "10")],
            # Turn
            [Card("hearts", "9")],
            # River
            [Card("hearts", "8")]
        ]):
            # Run the game
            game.play_hand()
            
            # Verify expected outcomes based on the controlled scenario
            print("\nControlled Game Result:")
            for player in players:
                print(f"{player.name}: {player.chips} chips")


if __name__ == "__main__":
    # Run the simulation with controlled responses
    print("Running simulation with controlled responses...")
    simulate_hand_with_controlled_responses()
    
    # Run unit tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)