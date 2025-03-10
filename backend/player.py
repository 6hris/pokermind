from enum import Enum
import random

class PlayerAction(Enum):
    """Possible actions a player can take during their turn."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


class PlayerStatus(Enum):
    """Possible statuses of a player during a game."""
    ACTIVE = "active"     
    FOLDED = "folded"     
    ALL_IN = "all_in"     
    OUT = "out"         


class Player:
    def __init__(self, name, is_human, chips, position):
        self.name = name
        self.chips = chips
        self.position = position
        self.hand = []
        self.status = PlayerStatus.ACTIVE
        self.current_bet = 0
        self.is_dealer = False
        self.is_sb = False
        self.is_bb = False
    
    def reset_for_hand(self):
        self.hand = []
        self.current_bet = 0
        self.status = PlayerStatus.ACTIVE if self.chips > 0 else PlayerStatus.OUT

    def recieve_cards(self, cards):
        self.hand = cards
    
    def place_bet(self, amount):
        if self.status != PlayerStatus.ACTIVE:
            raise ValueError(f"Player {self.name} cannot bet: {self.status.value}")
        
        actual_bet = min(amount, self.chips)

        self.chips -= actual_bet
        self.current_bet += actual_bet

        if self.chips == 0:
            self.status = PlayerStatus.ALL_IN
        
        return actual_bet
    
    def fold(self):
        self.status = PlayerStatus.FOLDED
    
    def get_available_actions(self, current_bet):
        actions = []
        if self.status != PlayerStatus.ACTIVE:
            return actions
        
        actions.append(PlayerAction.FOLD)

        if current_bet == 0:
            actions.append(PlayerAction.CHECK)
            if self.chips > 0:
                actions.append(PlayerAction.BET)
        else:
            if self.current_bet < current_bet:
                if self.chips >= current_bet - self.current_bet:
                    actions.append(PlayerAction.CALL)
                    actions.append(PlayerAction.RAISE)
            elif self.current_bet == current_bet:
                actions.append(PlayerAction.CHECK)
                if self.chips > 0:
                    actions.append(PlayerAction.RAISE)
        
        if self.chips > 0:
            actions.append(PlayerAction.ALL_IN)
        
        return actions
    
    def choose_action(self, current_bet, game_state=None):
        available_actions = self.get_available_actions(current_bet)
        if random.random() < 0.8 and PlayerAction.RAISE in available_actions:
            return PlayerAction.RAISE, current_bet * 2
        elif random.random() < 0.1 and PlayerAction.FOLD in available_actions:
            return PlayerAction.FOLD, 0
        elif PlayerAction.CHECK in available_actions:
            return PlayerAction.CHECK, 0
        elif PlayerAction.CALL in available_actions:
            return PlayerAction.CALL, 0
        elif self.chips <= 20 and PlayerAction.ALL_IN in available_actions:
            return PlayerAction.ALL_IN, self.chips
        elif PlayerAction.CALL in available_actions:
            return PlayerAction.CALL, 0
        else:
            return PlayerAction.FOLD, 0
        
        
