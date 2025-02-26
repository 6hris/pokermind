import random

SUITS = ["hearts", "diamonds", "clubs", "spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
        "J": 11, "Q": 12, "K": 13, "A": 14
    }

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.rank_value = RANK_VALUES[self.rank]

    def __str__(self) -> str:
        suit_symbols = {
            "hearts": "♥",
            "diamonds": "♦",
            "clubs": "♣",
            "spades": "♠"
        }
        return f"{self.rank}{suit_symbols[self.suit]}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, Card):
            raise TypeError("Can only compare with another Card object")
        return self.rank_value < other.rank_value
    

class Deck:
    def __init__(self):
        self.cards = []
        self.dealt_cards = []

        for suit in SUITS:
            for rank in RANKS:
                self.cards.append(Card(suit, rank))
    
    def __str__(self) -> str:
        """Return a string representation of the deck."""
        return f"Deck with {len(self.cards)} cards remaining"
    
    def shuffle(self):
        self.cards.extend(self.dealt_cards) # bring cards back to og amount
        self.dealt_cards = []

        random.shuffle(self.cards)
    
    def deal(self, count):
        if count > len(self.cards):
            raise ValueError(f"Cannot deal {count} cards, only {len(self.cards)} remaining")
        
        dealt = []
        for _ in range(count):
            card = self.cards.pop()
            dealt.append(card)
            self.dealt_cards.append(card)
        
        return dealt

    def deal_one(self):
        if not self.cards:
            return None
        
        return self.deal(1)[0]

    def burn(self):
        if self.cards:
            self.dealt_cards.append(self.cards.pop())
    
    def reset(self) -> None:
        self.__init__()

def format_cards(cards):
    return " ".join(str(card) for card in cards)
         
if __name__ == "__main__":
    deck = Deck()
    deck.shuffle()

    hand = deck.deal(2)
    print(f"Dealt hand: {format_cards(hand)}")

    deck.burn()
    flop = deck.deal(3)
    print(f"Flop: {format_cards(flop)}")

    deck.burn()
    turn = deck.deal_one()
    print(f"Turn: {turn}")

    deck.burn()
    river = deck.deal_one()
    print(f"River: {river}")

    print(f"full board: {format_cards(flop + [turn, river])}")
    print(f"Cards remaining: {deck}")
    

