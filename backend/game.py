from typing import List, Dict, Optional, Any
from deck import Card, Deck, format_cards
from player import Player, PlayerStatus, PlayerAction
from llm_player import LLMPlayer
from treys import Evaluator, Card as TreysCard
import asyncio
from enum import Enum

class GameStage(Enum):
    SETUP = "setup"
    DEALING = "dealing"
    PREFLOP = "pre-flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    HAND_COMPLETE = "hand_complete"

class GameEvent(Enum):
    GAME_STARTED = "game_started"
    HAND_STARTED = "hand_started"
    BLINDS_POSTED = "blinds_posted"
    HOLE_CARDS_DEALT = "hole_cards_dealt"
    BETTING_STARTED = "betting_started"
    PLAYER_ACTION = "player_action"
    COMMUNITY_CARDS_DEALT = "community_cards_dealt"
    HAND_COMPLETE = "hand_complete"
    GAME_COMPLETE = "game_complete"

class Game:
    def __init__(self, players: List[Player], sb: int, bb: int, callback=None, 
                 delay_between_actions: float = 1.0,
                 delay_between_stages: float = 2.0,
                 delay_after_hand: float = 3.0):
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
        self.current_stage = GameStage.SETUP
        self.callback = callback
        self.hand_number = 0
        
        # Game speed controls (in seconds)
        self.delay_between_actions = delay_between_actions
        self.delay_between_stages = delay_between_stages
        self.delay_after_hand = delay_after_hand
        
    async def emit_event(self, event_type: GameEvent, data: Dict[str, Any]):
        """Emit game events through the callback if provided"""
        if self.callback:
            await self.callback(event_type.value, data)
    
    def set_player_positions(self):
        num_players = len(self.players)
        active_players = [p for p in self.players if p.status != PlayerStatus.OUT]
        
        if len(active_players) < 2:
            return  # Not enough active players to set positions

        for player in self.players:
            player.is_dealer = False
            player.is_sb = False
            player.is_bb = False
        
        # Set dealer
        self.players[self.dealer_pos].is_dealer = True
        
        # Find SB position (next active player after dealer)
        sb_pos = (self.dealer_pos + 1) % num_players
        while self.players[sb_pos].status == PlayerStatus.OUT:
            sb_pos = (sb_pos + 1) % num_players
            # Safety check to avoid infinite loops
            if sb_pos == self.dealer_pos:
                break
                
        self.players[sb_pos].is_sb = True
        
        # Find BB position (next active player after SB)
        bb_pos = (sb_pos + 1) % num_players
        while self.players[bb_pos].status == PlayerStatus.OUT:
            bb_pos = (bb_pos + 1) % num_players
            # Safety check to avoid infinite loops
            if bb_pos == sb_pos:
                break
                
        self.players[bb_pos].is_bb = True
    
    def rotate_dealer(self):
        num_players = len(self.players)
        active_players = [p for p in self.players if p.status != PlayerStatus.OUT]
        
        if len(active_players) < 2:
            return  # Not enough active players to rotate
            
        # Find next active player to be the dealer
        next_pos = (self.dealer_pos + 1) % num_players
        while self.players[next_pos].status == PlayerStatus.OUT:
            next_pos = (next_pos + 1) % num_players
            # Safety check to avoid infinite loops
            if next_pos == self.dealer_pos:
                break
                
        self.dealer_pos = next_pos
        self.set_player_positions()

    async def deal_hole_cards(self):
        # Pause before dealing cards
        await asyncio.sleep(self.delay_between_stages)
        
        for player in self.players:
            if player.status != PlayerStatus.OUT:
                player.recieve_cards(self.deck.deal(2))
                # Small delay between each player getting cards for visual effect
                await asyncio.sleep(0.2)
        
        # Emit event with hole cards for each player
        await self.emit_event(GameEvent.HOLE_CARDS_DEALT, {
            "players": [
                {
                    "name": p.name, 
                    "hole_cards": format_cards(p.hand) if p.hand else ""
                } 
                for p in self.players
            ]
        })
        
        # Give time for players to see their cards
        await asyncio.sleep(self.delay_between_stages)
    
    async def post_blinds(self):
        num_players = len(self.players)
        active_players = [p for p in self.players if p.status == PlayerStatus.ACTIVE]
        
        if len(active_players) < 2:
            # Not enough active players to continue
            raise ValueError("Not enough active players to continue the game")
            
        # Find the next ACTIVE player after dealer for small blind
        sb_pos = (self.dealer_pos + 1) % num_players
        attempts = 0
        # Skip players with OUT status
        while self.players[sb_pos].status != PlayerStatus.ACTIVE:
            sb_pos = (sb_pos + 1) % num_players
            attempts += 1
            # Safety check to prevent infinite loops
            if attempts >= num_players:
                raise ValueError("Could not find an eligible player for small blind")
            
        sb_player = self.players[sb_pos]
        sb_bet = sb_player.place_bet(self.sb)
        self.pot += sb_bet

        # Find the next ACTIVE player after SB for big blind
        bb_pos = (sb_pos + 1) % num_players
        attempts = 0
        # Skip players with OUT status
        while self.players[bb_pos].status != PlayerStatus.ACTIVE:
            bb_pos = (bb_pos + 1) % num_players
            attempts += 1
            # Safety check to prevent infinite loops
            if attempts >= num_players:
                raise ValueError("Could not find an eligible player for big blind")
            
        bb_player = self.players[bb_pos]
        bb_bet = bb_player.place_bet(self.bb)
        self.pot += bb_bet

        self.current_bet = self.bb
        
        await self.emit_event(GameEvent.BLINDS_POSTED, {
            "sb_player": sb_player.name,
            "sb_amount": sb_bet,
            "bb_player": bb_player.name,
            "bb_amount": bb_bet,
            "pot": self.pot
        })
    
    async def deal_community_cards(self, count, stage: GameStage):
        # Pause before dealing community cards
        await asyncio.sleep(self.delay_between_stages)
        
        self.deck.burn()
        new_cards = self.deck.deal(count)
        self.community_cards.extend(new_cards)
        
        await self.emit_event(GameEvent.COMMUNITY_CARDS_DEALT, {
            "stage": stage.value,
            "new_cards": format_cards(new_cards),
            "all_cards": format_cards(self.community_cards)
        })
        
        # Give time for players to see the new community cards
        await asyncio.sleep(self.delay_between_stages)
    
    def get_starting_player_index(self, round_type):
        if round_type == "pre-flop":
            start_pos = (self.dealer_pos + 3) % len(self.players)
        else:
            start_pos = (self.dealer_pos + 1) % len(self.players)
        
        for i in range(len(self.players)):
            idx = (start_pos + i) % len(self.players)
            # Skip both FOLDED and OUT players
            if self.players[idx].status != PlayerStatus.FOLDED and self.players[idx].status != PlayerStatus.OUT:
                return idx
        
        return -1 

    async def betting_round(self, round_type):
        await self.emit_event(GameEvent.BETTING_STARTED, {
            "round": round_type,
            "current_bet": self.current_bet,
        })
        
        start_idx = self.get_starting_player_index(round_type)

        # Check if we have enough active players (not FOLDED or OUT)
        active_non_out_players = [p for p in self.players if p.status != PlayerStatus.FOLDED and p.status != PlayerStatus.OUT]
        if start_idx == -1 or len(active_non_out_players) <= 1:
            return
        
        if round_type != "pre-flop":
            self.current_bet = 0
            self.last_raise = self.bb

        self.hand_context.append(f"current round: {round_type}")
        
        num_players = len(self.players)
        while True:
            # Filter out both FOLDED and OUT players
            active_players = [p for p in self.players if p.status != PlayerStatus.FOLDED and p.status != PlayerStatus.OUT]

            if len(active_players) <= 1:
                break
            
            changed_bet = False
            curr_idx = start_idx
            for _ in range(num_players):
                player = self.players[curr_idx]
                if (player.status != PlayerStatus.FOLDED and player.status != PlayerStatus.OUT and player.chips > 0 and (player.current_bet < self.current_bet or self.current_bet == 0)):
                    if isinstance(player, LLMPlayer):
                        action, amount = await player.choose_action(self.current_bet, self.get_player_context(player))
                    else:
                        action, amount = player.choose_action(self.current_bet)
                    
                    action_result = {
                        "player": player.name,
                        "action": action.value,
                        "amount": 0
                    }
                    
                    if action == PlayerAction.FOLD:
                        self.hand_context.append(f"{player.name} FOLDS")
                        player.fold()
                        print(f"{player.name} {action.value}")
                    elif action == PlayerAction.CHECK:
                        self.hand_context.append(f"{player.name} checks")
                        print(f"{player.name} {action.value}")
                    elif action == PlayerAction.CALL:
                        call_amount = self.current_bet - player.current_bet
                        actual_bet = player.place_bet(call_amount)
                        action_result["amount"] = actual_bet
                        self.hand_context.append(f"{player.name} calls {actual_bet}")
                        print(f"{player.name} {action.value} {actual_bet}")
                    elif action == PlayerAction.BET:
                        changed_bet = True
                        bet_amount = max(self.min_bet, amount)
                        actual_bet = player.place_bet(bet_amount)
                        action_result["amount"] = actual_bet
                        self.last_raise = bet_amount
                        self.current_bet = player.current_bet
                        self.hand_context.append(f"{player.name} bets {actual_bet}")
                        print(f"{player.name} {action.value} {actual_bet}")
                    elif action == PlayerAction.RAISE:
                        changed_bet = True
                        raise_amount = max(self.last_raise, amount)
                        total_bet = self.current_bet + raise_amount
                        call_amount = self.current_bet - player.current_bet
                        player.place_bet(call_amount + raise_amount)
                        action_result["amount"] = call_amount + raise_amount
                        self.current_bet = player.current_bet
                        self.hand_context.append(f"{player.name} raises {raise_amount}")
                        print(f"{player.name} {action.value} {raise_amount}")
                    elif action == PlayerAction.ALL_IN:
                        changed_bet = True
                        actual_bet = player.place_bet(player.chips)
                        action_result["amount"] = actual_bet
                        if player.current_bet > self.current_bet:
                            self.current_bet = player.current_bet
                        self.hand_context.append(f"{player.name} all-in {actual_bet}")
                        print(f"{player.name} {action.value} {actual_bet}")
                    
                    # Emit player action event
                    await self.emit_event(GameEvent.PLAYER_ACTION, {
                        "player": player.name,
                        "action": action.value,
                        "amount": action_result["amount"],
                        "remaining_chips": player.chips,
                        "pot": self.pot,
                        "current_bet": self.current_bet
                    })
                    
                    # Add a delay between player actions for better UI experience
                    await asyncio.sleep(self.delay_between_actions)
                    
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

    async def play_hand(self):
        self.hand_number += 1
        for player in self.players:
            player.reset_for_hand()
            
        # Check if we have enough active players to continue
        active_players = [p for p in self.players if p.status != PlayerStatus.OUT]
        if len(active_players) < 2:
            print(f"Not enough active players to continue. Only {len(active_players)} players with chips.")
            return
            
        self.community_cards = []
        self.pot = 0
        self.deck.shuffle()
        self.rotate_dealer()
        self.hand_context = []
        print(f"\n===== NEW HAND #{self.hand_number} =====")
        
        await self.emit_event(GameEvent.HAND_STARTED, {
            "hand_number": self.hand_number,
            "dealer": self.players[self.dealer_pos].name,
            "small_blind": self.sb,
            "big_blind": self.bb,
            "players": [{
                "name": p.name, 
                "chips": p.chips, 
                "position": p.position,
                "is_dealer": p.is_dealer,
                "is_sb": p.is_sb,
                "is_bb": p.is_bb
            } for p in self.players]
        })

        try:
            await self.post_blinds()
            await self.deal_hole_cards()
        except ValueError as e:
            print(f"Error during hand setup: {e}")
            return  # Skip this hand and move to the next

        for player in self.players:
            if player.hand:
                print(f"{player.name}'s hand: {format_cards(player.hand)}")

        # Pre-flop betting
        self.current_stage = GameStage.PREFLOP
        await self.betting_round("pre-flop")
        active_players = [p for p in self.players if p.status != PlayerStatus.FOLDED and p.status != PlayerStatus.OUT]
        if len(active_players) <= 1:
            await self.complete_hand()
            return

        # Flop
        self.current_stage = GameStage.FLOP
        await self.deal_community_cards(3, GameStage.FLOP)
        print(f"\n--- Flop: {format_cards(self.community_cards)} ---")
        await self.betting_round("flop")
        active_players = [p for p in self.players if p.status != PlayerStatus.FOLDED and p.status != PlayerStatus.OUT]
        if len(active_players) <= 1:
            await self.complete_hand()
            return

        # Turn
        self.current_stage = GameStage.TURN
        await self.deal_community_cards(1, GameStage.TURN)
        print(f"\n--- Turn: {format_cards(self.community_cards)} ---")
        await self.betting_round("turn")
        active_players = [p for p in self.players if p.status != PlayerStatus.FOLDED and p.status != PlayerStatus.OUT]
        if len(active_players) <= 1:
            await self.complete_hand()
            return

        # River
        self.current_stage = GameStage.RIVER
        await self.deal_community_cards(1, GameStage.RIVER)
        print(f"\n--- River: {format_cards(self.community_cards)} ---")
        await self.betting_round("river")
        
        await self.complete_hand()
    
    async def complete_hand(self):
        self.current_stage = GameStage.SHOWDOWN
        active_players = [p for p in self.players if p.status != PlayerStatus.FOLDED and p.status != PlayerStatus.OUT]
        
        result = {
            "pot": self.pot,
            "community_cards": format_cards(self.community_cards),
            "winners": [],
            "is_split_pot": False,
            "players": [{
                "name": p.name,
                "chips": p.chips,
                "status": p.status.value
            } for p in self.players]
        }
        
        if len(active_players) == 1:
            active_players[0].chips += self.pot
            print(f"\n{active_players[0].name} wins {self.pot} chips (uncontested)")
            result["winners"] = [{
                "name": active_players[0].name,
                "winnings": self.pot,
                "hand": format_cards(active_players[0].hand),
                "description": "uncontested"
            }]
        elif len(active_players) > 1:
            print("\n=== SHOWDOWN ===")
            scores = [(p, self.evaluate_hand(p.hand)) for p in active_players]
            best_score = min(score for _, score in scores) 
            winners = [p for p, score in scores if score == best_score]
            pot_share = self.pot // len(winners) 
            
            result["is_split_pot"] = len(winners) > 1
            for winner in winners:
                winner.chips += pot_share
                result["winners"].append({
                    "name": winner.name,
                    "winnings": pot_share,
                    "hand": format_cards(winner.hand),
                    "description": "split pot" if len(winners) > 1 else "best hand"
                })
            
            winner_names = ", ".join(p.name for p in winners)
            if len(winners) > 1:
                print(f"\nSplit pot ({self.pot} chips) between: {winner_names}")
            else:
                print(f"\n{winners[0].name} wins {self.pot} chips")

        self.pot = 0
        
        await self.emit_event(GameEvent.HAND_COMPLETE, result)
        self.current_stage = GameStage.HAND_COMPLETE
        
        # Add a longer delay after hand completion to let users process the results
        await asyncio.sleep(self.delay_after_hand)

    async def play_game(self, num_hands):
        """Play a specific number of hands"""
        for i in range(num_hands):
            await self.play_hand()
            
            # Check if there's only one player with chips left
            players_with_chips = [p for p in self.players if p.chips > 0]
            if len(players_with_chips) <= 1:
                break
        
        # Game complete
        await self.emit_event(GameEvent.GAME_COMPLETE, {
            "hands_played": self.hand_number,
            "players": [{
                "name": p.name,
                "chips": p.chips,
                "is_winner": p.chips > 0
            } for p in self.players]
        })
        
        return self.players