from pydantic import BaseModel, ConfigDict

class UserStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    chips_balance: int
    total_rounds: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    net_payout: int
