import random
from typing import Any
from app.schemas.game import CardSchema, HandSchema, DealerHandSchema

SUITS = ["H", "D", "C", "S"]  # Hearts, Diamonds, Clubs, Spades
VALUES = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

def get_card_numeric_value(value: str) -> int:
    if value in ["J", "Q", "K"]:
        return 10
    if value == "A":
        return 11
    return int(value)

def calculate_hand_value(cards: list[dict[str, Any]]) -> int:
    total = 0
    aces = 0
    for card in cards:
        val = card["value"]
        if val == "A":
            aces += 1
            total += 11
        else:
            total += get_card_numeric_value(val)
            
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

def is_blackjack(cards: list[dict[str, Any]]) -> bool:
    if len(cards) != 2:
        return False
    val1 = get_card_numeric_value(cards[0]["value"])
    val2 = get_card_numeric_value(cards[1]["value"])
    return (val1 == 11 and val2 == 10) or (val1 == 10 and val2 == 11)

def create_shuffled_deck(num_decks: int = 6) -> list[dict[str, Any]]:
    deck = []
    for _ in range(num_decks):
        for suit in SUITS:
            for val in VALUES:
                deck.append({"suit": suit, "value": val})
    random.shuffle(deck)
    return deck

class GameService:
    @staticmethod
    def initialize_round(deck: list[dict[str, Any]], bet: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        # Draw 2 for player, 2 for dealer
        p_cards = [deck.pop(), deck.pop()]
        d_cards = [deck.pop(), deck.pop()]
        
        # Check initial statuses
        p_val = calculate_hand_value(p_cards)
        p_status = "blackjack" if is_blackjack(p_cards) else "playing"
        
        player_hands = [{
            "cards": p_cards,
            "bet": bet,
            "status": p_status
        }]
        
        d_status = "blackjack" if is_blackjack(d_cards) else "playing"
        dealer_hand = {
            "cards": d_cards,
            "status": d_status
        }
        
        return deck, player_hands, dealer_hand

    @staticmethod
    def process_dealer_turn(deck: list[dict[str, Any]], dealer_hand: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        # Dealer must hit until 17 or higher
        d_cards = dealer_hand["cards"]
        val = calculate_hand_value(d_cards)
        
        while val < 17:
            d_cards.append(deck.pop())
            val = calculate_hand_value(d_cards)
            
        dealer_hand["cards"] = d_cards
        if val > 21:
            dealer_hand["status"] = "busted"
        elif is_blackjack(d_cards):
            dealer_hand["status"] = "blackjack"
        else:
            dealer_hand["status"] = "stood"
            
        return deck, dealer_hand

    @staticmethod
    def resolve_payouts(player_hands: list[dict[str, Any]], dealer_hand: dict[str, Any], insurance_bet: int | None = None) -> tuple[int, str]:
        total_payout = 0
        outcomes = []
        
        d_cards = dealer_hand["cards"]
        d_val = calculate_hand_value(d_cards)
        d_bj = is_blackjack(d_cards)
        d_busted = dealer_hand["status"] == "busted"
        
        # 1. Resolve Insurance Side Bet
        # Insurance pays 2:1 if dealer has blackjack. Otherwise it's lost.
        if insurance_bet is not None and insurance_bet > 0:
            if d_bj:
                total_payout += insurance_bet * 3  # Returned insurance bet + 2:1 winnings
            # if no dealer blackjack, insurance bet is lost (0 returned)

        # 2. Resolve Main Hand(s)
        for idx, hand in enumerate(player_hands):
            h_cards = hand["cards"]
            h_val = calculate_hand_value(h_cards)
            h_bj = is_blackjack(h_cards)
            h_bet = hand["bet"]
            
            # If player busted, hand is lost (already marked or resolved)
            if h_val > 21:
                hand["status"] = "busted"
                outcomes.append("lost")
                continue
                
            # If player has blackjack
            if h_bj:
                if d_bj:
                    # Push
                    hand["status"] = "push"
                    total_payout += h_bet
                    outcomes.append("push")
                else:
                    # Player wins 3:2
                    hand["status"] = "blackjack"
                    total_payout += int(h_bet + (h_bet * 1.5))
                    outcomes.append("won")
                continue

            # If dealer has blackjack (and player doesn't)
            if d_bj:
                hand["status"] = "lost"
                outcomes.append("lost")
                continue

            # If dealer busted (and player didn't)
            if d_busted:
                hand["status"] = "won"
                total_payout += h_bet * 2
                outcomes.append("won")
                continue

            # Compare totals
            if h_val > d_val:
                hand["status"] = "won"
                total_payout += h_bet * 2
                outcomes.append("won")
            elif h_val < d_val:
                hand["status"] = "lost"
                outcomes.append("lost")
            else:
                hand["status"] = "push"
                total_payout += h_bet
                outcomes.append("push")
                
        # Overall outcome label
        if len(outcomes) == 1:
            overall_outcome = f"player_{outcomes[0]}"
        else:
            # Multi-hand split outcomes
            unique_outcomes = set(outcomes)
            if len(unique_outcomes) == 1:
                overall_outcome = f"player_{outcomes[0]}"
            else:
                overall_outcome = "split_mixed"
                
        return total_payout, overall_outcome
