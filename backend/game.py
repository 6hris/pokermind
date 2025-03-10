from typing import List
from deck import Card, Deck, format_cards
from player import Player, PlayerStatus, PlayerAction
from treys import Evaluator, Card as TreysCard

class Game:
    def __init__(self, players: List[Player], sb: int, bb: int):
        self.players = players
        self.sb = sb
        self.bb = bb
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.dealer_pos = 0
        self.min_bet = bb
        self.last_raise = bb
        self.evaluator = Evaluator()
        self.hand_context = []

    
    def set_player_positions(self):
        num_players = len(self.players)

        for player in self.players:
            player.is_dealer = False
            player.is_sb = False
            player.is_bb = False
        
        self.players[self.dealer_pos].is_dealer = True
        self.players[(self.dealer_pos + 1) % num_players].is_sb = True
        self.players[(self.dealer_pos + 2) % num_players].is_bb = True
    
    def rotate_dealer(self):
        self.dealer_pos = (self.dealer_pos + 1) % len(self.players)
        self.set_player_positions()

    def deal_hole_cards(self):
        for player in self.players:
            if player.status != PlayerStatus.OUT:
                player.recieve_cards(self.deck.deal(2))
    
    def post_blinds(self):
        num_players = len(self.players)

        # small blind
        sb_bet = self.players[(self.dealer_pos + 1) % num_players].place_bet(self.sb)
        self.pot += sb_bet

        # big blind
        bb_bet = self.players[(self.dealer_pos + 2) % num_players].place_bet(self.bb)
        self.pot += bb_bet

        self.current_bet = self.bb
    
    def deal_community_cards(self, count):
        self.deck.burn()
        self.community_cards.extend(self.deck.deal(count))
    
    def get_starting_player_index(self, round_type):
        if round_type == "pre-flop":
            start_pos = (self.dealer_pos + 3) % len(self.players)
        else:
            start_pos = (self.dealer_pos + 1) % len(self.players)
        
        for i in range(len(self.players)):
            idx = (start_pos + i) % len(self.players)
            if self.players[idx].status != PlayerStatus.FOLDED:
                return idx
        
        return -1 

    def betting_round(self, round_type):
        start_idx = self.get_starting_player_index(round_type)

        if start_idx == -1 or len([p for p in self.players if p.status != PlayerStatus.FOLDED]) <= 1:
            return
        
        if round_type != "pre-flop":
            self.current_bet = 0
            self.last_raise = self.bb

        self.hand_context.append(f"current round: {round_type}")
        
        num_players = len(self.players)
        while True:
            active_players = [p for p in self.players if p.status != PlayerStatus.FOLDED]

            if len(active_players) <= 1:
                break
            
            changed_bet = False
            curr_idx = start_idx
            for _ in range(num_players):
                player = self.players[curr_idx]
                if (player.status != PlayerStatus.FOLDED and player.chips > 0 and (player.current_bet < self.current_bet or self.current_bet == 0)):
                    action, amount = player.choose_action(self.current_bet, "game_state_placeholder")
                    print(f"{player.name} {action.value}")
                    if action == PlayerAction.FOLD:
                        self.hand_context.append(f"{player.name} FOLDS")
                        player.fold()
                    elif action == PlayerAction.CHECK:
                        print(f"{player.name} checks")
                        self.hand_context.append(f"{player.name} checks")
                        pass
                    elif action == PlayerAction.CALL:
                        call_amount = self.current_bet - player.current_bet
                        actual_bet = player.place_bet(call_amount)
                        print(f"{player.name} calls {actual_bet}")
                        self.hand_context.append(f"{player.name} calls {actual_bet}")
                    elif action == PlayerAction.BET:
                        changed_bet = True
                        bet_amount = max(self.min_bet, amount)
                        actual_bet = player.place_bet(bet_amount)
                        self.last_raise = bet_amount
                        self.current_bet = player.current_bet
                        print(f"{player.name} bets {actual_bet}")
                        self.hand_context.append(f"{player.name} bets {actual_bet}")
                    elif action == PlayerAction.RAISE:
                        changed_bet = True
                        raise_amount = max(self.last_raise, amount)
                        player.place_bet(raise_amount)
                        self.current_bet = player.current_bet
                        print(f"{player.name} raises {raise_amount}")
                        self.hand_context.append(f"{player.name} raises {raise_amount}")
                    elif action == PlayerAction.ALL_IN:
                        changed_bet = True
                        actual_bet = player.place_bet(player.chips)
                        if player.current_bet > self.current_bet:
                            self.current_bet = player.current_bet
                        print(f"{player.name} all-in {actual_bet}")
                        self.hand_context.append(f"{player.name} all-in {actual_bet}")
                curr_idx = (curr_idx + 1) % num_players
        
            if not changed_bet:
                break

        for player in self.players:
            self.pot += player.current_bet
            player.current_bet = 0
    
    def get_hand_context(self) -> dict:
        player_summaries = []
        for p in self.players:
            player_summaries.append({
                "name": p.name,
                "chips": p.chips,
                "status": p.status.value,
                "current_bet": p.current_bet,
            })
        
        return {
            "community_cards": format_cards(self.community_cards),
            "pot": self.pot,
            "players": player_summaries,
            "actions_so_far": list(self.hand_context)
        }
    
    def get_player_context(self, player: Player) -> dict:
        public_context = self.get_hand_context()

        if player.status != PlayerStatus.FOLDED:
            hole_cards_str = "".join([card.to_treys_str() for card in player.hand])
        else:
            hole_cards_str = "" 

        call_amount = max(0, self.current_bet - player.current_bet)
        min_raise = max(self.last_raise, self.bb) if self.current_bet > 0 else self.bb

        player_context = {
            "player_name": player.name,
            "player_chips": player.chips,
            "player_status": player.status.value,
            "hole_cards": hole_cards_str,
            "call_amount": call_amount,
            "min_raise": min_raise,
            "community_cards": public_context["community_cards"],
            "pot": public_context["pot"],
            "players_summary": public_context["players"],   
            "actions_so_far": public_context["actions_so_far"]
        }

        return player_context

    
    def evaluate_hand(self, hand: List[Card]):
        treys_hand = [TreysCard.new(card.to_treys_str()) for card in hand]
        treys_community = [TreysCard.new(card.to_treys_str()) for card in self.community_cards]

        return self.evaluator.evaluate(treys_community, treys_hand)
    
    def evaluate(self, hand):
        ranks = '23456789TJQKA'
        if len(hand) > 5: return max([self.evaluate(hand[:i] + hand[i+1:]) for i in range(len(hand))])
        score, ranks = zip(*sorted((cnt, rank) for rank, cnt in {ranks.find(r): ''.join(hand).count(r) for r, _ in hand}.items())[::-1])
        if len(score) == 5:
            if ranks[0:2] == (12, 3): ranks = (3, 2, 1, 0, -1)
            score = ([(1,),(3,1,2)],[(3,1,3),(5,)])[len({suit for _, suit in hand}) == 1][ranks[0] - ranks[4] == 4]
        return score, ranks

    def play_hand(self):
        for player in self.players:
            player.reset_for_hand()
        self.community_cards = []
        self.pot = 0
        self.deck.shuffle()
        self.rotate_dealer()
        self.hand_context = []
        print("\n===== NEW HAND =====")
        print(f"Dealer: {self.players[self.dealer_pos].name}")
    

        self.post_blinds()
        self.deal_hole_cards()

        for player in self.players:
            if player.hand:
                print(f"{player.name}'s hand: {format_cards(player.hand)}")

        for round_type, card_count in [("pre-flop", 0), ("flop", 3), ("turn", 1), ("river", 1)]:
            self.betting_round(round_type)
            active_players = [p for p in self.players if p.status != PlayerStatus.FOLDED]
            if len(active_players) <= 1:
                break
            if card_count > 0:
                self.deal_community_cards(card_count)
                print(f"\n--- {round_type.capitalize()}: {format_cards(self.community_cards)} ---")
        
        active_players = [p for p in self.players if p.status != PlayerStatus.FOLDED]
        if len(active_players) == 1:
            active_players[0].chips += self.pot
            print(f"\n{active_players[0].name} wins {self.pot} chips (uncontested)")
        elif len(active_players) > 1:
            print("\n=== SHOWDOWN ===")
            scores = [(p, self.evaluate_hand(p.hand)) for p in active_players]
            best_score = min(score for _, score in scores) 
            winners = [p for p, score in scores if score == best_score]
            pot_share = self.pot // len(winners) 
            
            winner_names = ", ".join(p.name for p in winners)
            if len(winners) > 1:
                print(f"\nSplit pot ({self.pot} chips) between: {winner_names}")
            else:
                print(f"\n{winners[0].name} wins {self.pot} chips")

            for winner in winners:
                winner.chips += pot_share
        self.pot = 0



    



    
