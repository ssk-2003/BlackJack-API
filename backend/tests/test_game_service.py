from app.services.game_service import (
    calculate_hand_value,
    is_blackjack,
    GameService
)

def test_calculate_hand_value():
    # Hard hand
    assert calculate_hand_value([{"suit": "H", "value": "10"}, {"suit": "D", "value": "5"}]) == 15
    
    # Soft Ace
    assert calculate_hand_value([{"suit": "H", "value": "A"}, {"suit": "D", "value": "5"}]) == 16
    
    # Dual Aces reducing to hard total
    assert calculate_hand_value([{"suit": "H", "value": "A"}, {"suit": "D", "value": "A"}, {"suit": "C", "value": "9"}]) == 21
    assert calculate_hand_value([{"suit": "H", "value": "A"}, {"suit": "D", "value": "A"}, {"suit": "C", "value": "A"}]) == 13
    
    # Face cards
    assert calculate_hand_value([{"suit": "H", "value": "K"}, {"suit": "D", "value": "Q"}]) == 20

def test_is_blackjack():
    assert is_blackjack([{"suit": "H", "value": "A"}, {"suit": "D", "value": "10"}]) is True
    assert is_blackjack([{"suit": "H", "value": "A"}, {"suit": "D", "value": "J"}]) is True
    assert is_blackjack([{"suit": "H", "value": "9"}, {"suit": "D", "value": "Q"}]) is False
    assert is_blackjack([{"suit": "H", "value": "A"}, {"suit": "D", "value": "A"}]) is False

def test_initialize_round():
    # Setup controlled deck
    deck = [
        {"suit": "S", "value": "A"},  # Dealer card 2
        {"suit": "H", "value": "2"},  # Dealer card 1
        {"suit": "C", "value": "K"},  # Player card 2
        {"suit": "D", "value": "10"}, # Player card 1
    ]
    
    rem_deck, player_hands, dealer_hand = GameService.initialize_round(deck, 100)
    
    assert len(rem_deck) == 0
    # Player draws cards in reverse order (pop)
    # Player cards: "10" and "K"
    assert player_hands[0]["cards"][0]["value"] == "10"
    assert player_hands[0]["cards"][1]["value"] == "K"
    
    # Dealer cards: "2" and "A"
    assert dealer_hand["cards"][0]["value"] == "2"
    assert dealer_hand["cards"][1]["value"] == "A"

def test_resolve_payouts():
    # Push condition
    p_hands = [{"cards": [{"suit": "H", "value": "10"}, {"suit": "S", "value": "10"}], "bet": 50, "status": "stood"}]
    d_hand = {"cards": [{"suit": "D", "value": "K"}, {"suit": "C", "value": "Q"}], "status": "stood"}
    payout, outcome = GameService.resolve_payouts(p_hands, d_hand)
    assert payout == 50  # Bet returned
    assert outcome == "player_push"
    
    # Player win condition
    p_hands = [{"cards": [{"suit": "H", "value": "10"}, {"suit": "S", "value": "A"}], "bet": 50, "status": "blackjack"}]
    d_hand = {"cards": [{"suit": "D", "value": "8"}, {"suit": "C", "value": "Q"}], "status": "stood"}
    payout, outcome = GameService.resolve_payouts(p_hands, d_hand)
    assert payout == 125  # 50 + 1.5 * 50 = 125
    assert outcome == "player_won"
    
    # Player bust condition
    p_hands = [{"cards": [{"suit": "H", "value": "10"}, {"suit": "S", "value": "K"}, {"suit": "C", "value": "3"}], "bet": 50, "status": "stood"}]
    d_hand = {"cards": [{"suit": "D", "value": "8"}, {"suit": "C", "value": "Q"}], "status": "stood"}
    payout, outcome = GameService.resolve_payouts(p_hands, d_hand)
    assert payout == 0
    assert outcome == "player_lost"
