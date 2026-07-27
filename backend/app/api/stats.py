from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.game import Game
from app.models.round import Round
from app.schemas.stats import UserStatsResponse

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/me", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve all resolved rounds for user
    stmt = (
        select(Round)
        .join(Game)
        .filter(Game.user_id == current_user.id, Round.status == "resolved")
    )
    result = await db.execute(stmt)
    rounds = result.scalars().all()
    
    total_rounds = len(rounds)
    wins = 0
    losses = 0
    pushes = 0
    net_payout = 0
    
    for r in rounds:
        # Sum overall payouts versus bets to find net outcome
        net_payout += (r.payout - r.bet - (r.insurance_bet or 0))
        
        # Determine stats category
        if r.outcome == "player_won":
            wins += 1
        elif r.outcome == "player_lost":
            losses += 1
        elif r.outcome == "player_push":
            pushes += 1
        elif r.outcome == "split_mixed":
            # Count splitting outcome as win if total payout > initial investment, otherwise loss
            invested = r.bet + (r.insurance_bet or 0)
            # Find splits total cost: each split hand duplicates original bet
            # player_hands holds all split hands
            total_bet = sum(hand["bet"] for hand in r.player_hands)
            invested = total_bet + (r.insurance_bet or 0)
            if r.payout > invested:
                wins += 1
            elif r.payout < invested:
                losses += 1
            else:
                pushes += 1

    win_rate = (wins / total_rounds * 100) if total_rounds > 0 else 0.0

    return UserStatsResponse(
        username=current_user.username,
        chips_balance=current_user.chips_balance,
        total_rounds=total_rounds,
        wins=wins,
        losses=losses,
        pushes=pushes,
        win_rate=round(win_rate, 2),
        net_payout=net_payout
    )
