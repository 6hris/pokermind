from typing import List
from deck import Card, Deck, format_cards
from player import Player, PlayerStatus


class Game:
    def __init__(self, players: List[Player], sb, bb):
        self.players = players
        self.sb = sb
        self.bb = bb
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.betting_round = 0  # 0: pre-flop, 1: flop, 2: turn, 3: river
        self.dealer_pos = 0
    
    def set_player_positions(self):
        num_players = len(self.players)

        for player in self.players:
            player.is_dealer = False
            player.is_small_blind = False
            player.is_big_blind = False
        
        self.players[self.dealer_pos].is_dealer = True
        self.players[(self.dealer_pos + 1) % num_players].is_sb = True
        self.players[(self.dealer_pos + 2) % num_players].is_sb = True
    
    def rotate_dealer(self):
        self.dealer_pos = (self.dealer_pos + 1) % len(self.players)
        self.set_player_positions()

    def deal_hole_cards(self):
        for player in self.players:
            if player.status != PlayerStatus.OUT:
                player.recieve_cards(self.deck.deal(2))
