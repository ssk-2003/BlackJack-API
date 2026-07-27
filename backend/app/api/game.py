from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.game import Game
from app.models.round import Round
from app.models.action import Action
from app.schemas.game import (
    StartRoundRequest,
    ActionRequest,
    RoundResponse,
    HandSchema,
    DealerHandSchema,
    CardSchema
)
from app.services.game_service import (
    create_shuffled_deck,
    calculate_hand_value,
    is_blackjack,
    GameService
)

router = APIRouter(prefix="/game", tags=["game"])

def build_round_response(round_obj: Round) -> RoundResponse:
    # Hydrate hand values on the fly for response serialization
    player_hands_schema = []
    for hand in round_obj.player_hands:
        player_hands_schema.append(HandSchema(
            cards=[CardSchema(**c) for c in hand["cards"]],
            bet=hand["bet"],
            status=hand["status"],
            value=calculate_hand_value(hand["cards"])
        ))
        
    dealer_hand_schema = DealerHandSchema(
        cards=[CardSchema(**c) for c in round_obj.dealer_hand["cards"]],
        status=round_obj.dealer_hand["status"],
        value=calculate_hand_value(round_obj.dealer_hand["cards"])
    )
    
    return RoundResponse(
        id=round_obj.id,
        game_id=round_obj.game_id,
        bet=round_obj.bet,
        insurance_bet=round_obj.insurance_bet,
        player_hands=player_hands_schema,
        dealer_hand=dealer_hand_schema,
        status=round_obj.status,
        outcome=round_obj.outcome,
        payout=round_obj.payout,
        actions=[
            {
                "id": a.id,
                "action_type": a.action_type,
                "hand_index": a.hand_index,
                "card_drawn": a.card_drawn,
                "created_at": a.created_at
            }
            for a in round_obj.actions
        ],
        created_at=round_obj.created_at
    )

@router.post("/start", response_model=RoundResponse)
async def start_round(
    req: StartRoundRequest, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # 1. Check chip balance
    if current_user.chips_balance < req.bet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient chips. Current balance: {current_user.chips_balance}"
        )
        
    # 2. Get active game, or start one
    game_stmt = select(Game).filter(Game.user_id == current_user.id, Game.status == "active")
    game_res = await db.execute(game_stmt)
    game = game_res.scalars().first()
    
    if not game:
        game = Game(
            user_id=current_user.id,
            deck_state=create_shuffled_deck(),
            status="active"
        )
        db.add(game)
        await db.flush()
    else:
        # Check if there is an unresolved round
        round_stmt = select(Round).filter(Round.game_id == game.id, Round.status != "resolved")
        round_res = await db.execute(round_stmt)
        active_round = round_res.scalars().first()
        if active_round:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Finish the active round before starting a new one."
            )
            
    # Check deck size, reshuffle if low
    deck = game.deck_state
    if len(deck) < 52:
        deck = create_shuffled_deck()
        
    # 3. Deduct bet from player's balance
    current_user.chips_balance -= req.bet
    db.add(current_user)
    
    # 4. Draw cards
    deck, p_hands, d_hand = GameService.initialize_round(deck, req.bet)
    
    # Save deck back to Game
    game.deck_state = deck
    db.add(game)
    
    # 5. Create new Round
    new_round = Round(
        game_id=game.id,
        bet=req.bet,
        player_hands=p_hands,
        dealer_hand=d_hand,
        status="playing",
        payout=0
    )
    db.add(new_round)
    await db.flush()
    
    # 6. Check for natural Blackjacks immediately
    p_bj = is_blackjack(new_round.player_hands[0]["cards"])
    d_bj = is_blackjack(new_round.dealer_hand["cards"])
    
    if p_bj or d_bj:
        new_round.status = "resolved"
        payout, outcome = GameService.resolve_payouts(new_round.player_hands, new_round.dealer_hand)
        new_round.payout = payout
        new_round.outcome = outcome
        
        # Credit player balance with payout
        current_user.chips_balance += payout
        db.add(current_user)
        db.add(new_round)
        
    await db.commit()
    
    # Refresh to load relationships (actions)
    stmt = select(Round).options(selectinload(Round.actions)).filter(Round.id == new_round.id)
    res = await db.execute(stmt)
    refreshed_round = res.scalars().one()
    
    return build_round_response(refreshed_round)

@router.post("/action", response_model=RoundResponse)
async def play_action(
    req: ActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Find active round
    game_stmt = select(Game).filter(Game.user_id == current_user.id, Game.status == "active")
    game_res = await db.execute(game_stmt)
    game = game_res.scalars().first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active game session found.")
        
    round_stmt = select(Round).options(selectinload(Round.actions)).filter(
        Round.game_id == game.id, Round.status != "resolved"
    )
    round_res = await db.execute(round_stmt)
    active_round = round_res.scalars().first()
    if not active_round:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active round found.")
        
    deck = game.deck_state
    hand_idx = req.hand_index
    action_type = req.action_type.lower()
    
    if hand_idx < 0 or hand_idx >= len(active_round.player_hands):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hand index.")
        
    current_hand = active_round.player_hands[hand_idx]
    
    # Check if hand is already inactive
    if current_hand["status"] != "playing":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hand is already complete.")
        
    card_drawn_str = None
    
    # Process specific actions
    if action_type == "hit":
        card = deck.pop()
        current_hand["cards"].append(card)
        card_drawn_str = f"{card['suit']}_{card['value']}"
        
        val = calculate_hand_value(current_hand["cards"])
        if val > 21:
            current_hand["status"] = "busted"
            
    elif action_type == "stand":
        current_hand["status"] = "stood"
        
    elif action_type == "double":
        # Can only double with exactly 2 cards in hand
        if len(current_hand["cards"]) != 2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only double down with 2 cards.")
        if current_user.chips_balance < current_hand["bet"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient chips to double bet.")
            
        # Deduct extra bet
        current_user.chips_balance -= current_hand["bet"]
        db.add(current_user)
        
        current_hand["bet"] *= 2
        card = deck.pop()
        current_hand["cards"].append(card)
        card_drawn_str = f"{card['suit']}_{card['value']}"
        
        val = calculate_hand_value(current_hand["cards"])
        if val > 21:
            current_hand["status"] = "busted"
        else:
            current_hand["status"] = "stood"
            
    elif action_type == "split":
        # Can only split with 2 identical value/pip cards
        if len(current_hand["cards"]) != 2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only split with exactly 2 cards.")
        c1, c2 = current_hand["cards"][0], current_hand["cards"][1]
        val1 = get_card_numeric_value(c1["value"])
        val2 = get_card_numeric_value(c2["value"])
        
        # Split is allowed if values or raw faces are matching (e.g. 10 and J could technically split or face values match. Let's match values)
        if val1 != val2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cards must match in value to split.")
            
        if current_user.chips_balance < current_hand["bet"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient chips to split.")
            
        # Deduct chips
        current_user.chips_balance -= current_hand["bet"]
        db.add(current_user)
        
        # Split hands
        hand1 = {
            "cards": [c1, deck.pop()],
            "bet": current_hand["bet"],
            "status": "playing"
        }
        hand2 = {
            "cards": [c2, deck.pop()],
            "bet": current_hand["bet"],
            "status": "playing"
        }
        
        # Update player_hands list
        active_round.player_hands[hand_idx] = hand1
        active_round.player_hands.insert(hand_idx + 1, hand2)
        
    elif action_type == "insurance":
        # Only allowed on first decision and when dealer's visible card (1st card) is an Ace
        if len(active_round.actions) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insurance only available as the first action.")
        dealer_upcard = active_round.dealer_hand["cards"][0]
        if dealer_upcard["value"] != "A":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insurance only offered on dealer Ace.")
        if active_round.insurance_bet is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insurance already placed.")
            
        ins_bet = int(active_round.bet / 2)
        if current_user.chips_balance < ins_bet:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient chips for insurance.")
            
        current_user.chips_balance -= ins_bet
        db.add(current_user)
        active_round.insurance_bet = ins_bet
        
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown action type.")

    # Record action in DB
    action_log = Action(
        round_id=active_round.id,
        action_type=action_type,
        hand_index=hand_idx,
        card_drawn=card_drawn_str
    )
    db.add(action_log)
    
    # Save deck/game state
    game.deck_state = deck
    db.add(game)
    
    # ── Check if player's turn is fully finished ────────────────────────────────
    all_finished = True
    for hand in active_round.player_hands:
        if hand["status"] == "playing":
            all_finished = False
            break
            
    if all_finished:
        active_round.status = "dealer_turn"
        
        # Check if dealer needs to play (if player hasn't busted on all hands)
        any_not_busted = False
        for hand in active_round.player_hands:
            if hand["status"] != "busted":
                any_not_busted = True
                break
                
        if any_not_busted:
            deck, active_round.dealer_hand = GameService.process_dealer_turn(deck, active_round.dealer_hand)
            game.deck_state = deck
            db.add(game)
            
        # Resolve payout
        payout, outcome = GameService.resolve_payouts(
            active_round.player_hands, active_round.dealer_hand, active_round.insurance_bet
        )
        active_round.payout = payout
        active_round.outcome = outcome
        active_round.status = "resolved"
        
        # Pay player
        current_user.chips_balance += payout
        db.add(current_user)
        
    db.add(active_round)
    await db.commit()
    
    # Refresh to load actions relationships
    stmt = select(Round).options(selectinload(Round.actions)).filter(Round.id == active_round.id)
    res = await db.execute(stmt)
    refreshed_round = res.scalars().one()
    
    return build_round_response(refreshed_round)

@router.get("/history", response_model=list[RoundResponse])
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Round)
        .join(Game)
        .options(selectinload(Round.actions))
        .filter(Game.user_id == current_user.id)
        .order_by(Round.created_at.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    rounds = result.scalars().all()
    return [build_round_response(r) for r in rounds]
