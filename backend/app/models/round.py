from datetime import datetime, timezone
from sqlalchemy import ForeignKey, Integer, String, JSON, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Round(Base):
    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    bet: Mapped[int] = mapped_column(Integer, nullable=False)
    insurance_bet: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # State tracking
    # player_hands structure: [{"cards": [{"suit": "H", "value": "A"}, ...], "bet": 10, "status": "playing" | "stood" | "busted" | "won" | "lost" | "push" | "blackjack"}]
    player_hands: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    
    # dealer_hand structure: {"cards": [{"suit": "H", "value": "K"}], "status": "playing" | "blackjack" | "stood" | "busted"}
    dealer_hand: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="playing", nullable=False)  # playing, dealer_turn, resolved
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)  # overall result e.g. player_win, dealer_win, push, mixed (if split)
    payout: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Total net payout/returned coins
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="rounds")
    actions: Mapped[list["Action"]] = relationship("Action", back_populates="round", cascade="all, delete-orphan")
