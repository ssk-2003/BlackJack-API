from datetime import datetime, timezone
from sqlalchemy import ForeignKey, Integer, String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    deck_state: Mapped[dict] = mapped_column(JSON, nullable=False)  # List of cards remaining in deck
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, completed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="games")
    rounds: Mapped[list["Round"]] = relationship("Round", back_populates="game", cascade="all, delete-orphan")
