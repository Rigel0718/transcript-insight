from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field
if TYPE_CHECKING:
    from analyst_agent.react.logger import RunLogger

class Env(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # 임의 타입 허용 (RunLogger)
        frozen=True,                  
        populate_by_name=True          
    )
    user_id: str = "anonymous"
    work_dir: str = Field(".", alias="workdir")
    artifact_dir: str = Field("./artifacts", alias="artifact_dir")
    run_logger: Optional["RunLogger"] = None
