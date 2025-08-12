from typing import Literal, Optional
from pydantic import BaseModel, Field

class RouteDecision(BaseModel):
    action: Literal["to_gen_df", "to_gen_chart", "finish"] = Field(
        ..., description="Next action for the agent."
    )
    reason: str = Field(..., description="One concise sentence explaining the decision.")
    notes: Optional[str] = None