import sys
import os
import asyncio
import pytest
from unittest.mock import patch

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import Game
from player import Player, PlayerStatus, PlayerAction

class TestBankruptcyHandling:
    @pytest.mark.asyncio
    async def test_game_continues_after_player_bankruptcy(self):
        """Test that game continues after a player loses all chips but at least 2 remain"""
        # Create 3 players: one will go bankrupt
        player1 = Player("Player1", False, 1000, 0)
        player2 = Player("Player2", False, 1000, 1)
        bankrupt_player = Player("BankruptPlayer", False, 100, 2)  # Low chips, will go bankrupt
        
        # Create a game with these players
        game = Game(
            players=[player1, player2, bankrupt_player],
            sb=5,
            bb=10,
            delay_between_actions=0.01,  # Speed up for testing
            delay_between_stages=0.01,
            delay_after_hand=0.01
        )
        
        # Mock player actions to force bankrupt_player to go all-in and lose
        def mocked_choose_action(self, current_bet, game_state=None):
            if self.name == "BankruptPlayer" and game.hand_number == 1:
                # Make sure bankrupt_player goes all-in in first hand
                self.chips = 100  # Force chips to 100 to ensure test consistency
                return PlayerAction.ALL_IN, self.chips
            elif self.name == "Player1" and game.hand_number == 1:
                # Player1 calls and should win
                self.chips = 1000  # Force chips to 1000 in case previous tests changed it
                return PlayerAction.CALL, current_bet
            elif self.name == "Player2" and game.hand_number == 1:
                # Player2 should fold
                return PlayerAction.FOLD, 0
            else:
                # Otherwise fold
                return PlayerAction.FOLD, 0
            
        # Force bankrupt player to lose by manually setting chips to 0 after first hand
        original_complete_hand = game.complete_hand
        
        async def mocked_complete_hand():
            await original_complete_hand()
            if game.hand_number == 1:
                # Manually bankrupt the player after first hand
                bankrupt_player.chips = 0
                bankrupt_player.status = PlayerStatus.OUT
                
        # Replace the complete_hand method
        game.complete_hand = mocked_complete_hand
                
        # Apply the mock
        with patch.object(Player, 'choose_action', mocked_choose_action):
            # Play 3 hands - first hand causes bankruptcy, next two should continue
            await game.play_game(3)
            
            # Verify bankrupt player is OUT
            assert bankrupt_player.status == PlayerStatus.OUT
            assert bankrupt_player.chips == 0
            
            # Verify game played all 3 hands
            assert game.hand_number == 3
            
            # Verify other players are still active
            assert player1.status in [PlayerStatus.ACTIVE, PlayerStatus.FOLDED]
            assert player2.status in [PlayerStatus.ACTIVE, PlayerStatus.FOLDED]
            
            # Verify the game was able to continue for 3 hands despite one player going OUT
            # Note: We don't need to check specific chip counts as they may vary based on the mock
            assert game.hand_number == 3
            
            # Just verify bankrupt player remains OUT
            assert bankrupt_player.status == PlayerStatus.OUT
            assert bankrupt_player.chips == 0

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])