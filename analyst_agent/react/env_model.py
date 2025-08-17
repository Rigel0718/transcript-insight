from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel
if TYPE_CHECKING:
    from analyst_agent.react.logger import RunLogger

class Env(BaseModel):
    user_id: str = "anonymous"
    workdir: str = "."
    artifact_dir: str = "./artifacts"
    run_logger: Optional["RunLogger"] = None

    class Config:
        frozen = True
        validate_assignment = False