from datetime import datetime, timezone
from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Action(Base):
    __tablename__ = "actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    round_id: Mapped[int] = mapped_column(Integer, ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)  # hit, stand, double, split, insurance
    hand_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # which hand index the action was applied to (mostly 0, unless split)
    card_drawn: Mapped[str | None] = mapped_column(String(10), nullable=True)  # card visual representation like "H_A", "S_10", or None
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    round: Mapped["Round"] = relationship("Round", back_populates="actions")
