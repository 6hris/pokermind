from enum import Enum

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
        self.is_human = is_human
        self.position = position
        self.hand = []
        self.status = PlayerStatus.ACTIVE
        self.current_bet = 0
    
    def reset_for_hand(self):
        self.hand = []
        self.current_bet = 0
        if self.chips > 0:
            self.status = PlayerStatus.ACTIVE
        else:
            self.status = PlayerStatus.OUT

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
    
    def can_make_action(self, action, current_bet):
        if self.status != PlayerStatus.ACTIVE:
            return False
        
        if action == PlayerAction.FOLD:
            return True
        
        if action == PlayerAction.CHECK:
            return self.current_bet == current_bet
        
        if action == PlayerAction.CALL:
            return self.current_bet < current_bet and self.chips > 0

        if action == PlayerAction.RAISE:
            return current_bet > 0 and self.chips > 0
        
        if action == PlayerAction.ALL_IN:
            return self.chips > 0
        
        return False
    
    def get_available_actions(self, current_bet):
        return [action for action in PlayerAction if self.can_make_action(action, current_bet)]
        
