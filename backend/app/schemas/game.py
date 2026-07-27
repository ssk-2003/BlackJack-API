from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class CardSchema(BaseModel):
    suit: str  # H, D, C, S
    value: str  # 2-10, J, Q, K, A

class HandSchema(BaseModel):
    cards: list[CardSchema]
    bet: int
    status: str  # playing, stood, busted, won, lost, push, blackjack
    value: int  # Current calculated hand value

class DealerHandSchema(BaseModel):
    cards: list[CardSchema]
    status: str  # playing, stood, busted, blackjack
    value: int

class ActionRequest(BaseModel):
    action_type: str = Field(..., description="hit, stand, double, split, insurance")
    hand_index: int = Field(0, description="Index of hand to act on, relevant after split")

class StartRoundRequest(BaseModel):
    bet: int = Field(..., ge=10, le=1000)

class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_type: str
    hand_index: int
    card_drawn: str | None
    created_at: datetime

class RoundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: int
    bet: int
    insurance_bet: int | None
    player_hands: list[HandSchema]
    dealer_hand: DealerHandSchema
    status: str
    outcome: str | None
    payout: int
    actions: list[ActionResponse]
    created_at: datetime

class GameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    created_at: datetime
    ended_at: datetime | None
