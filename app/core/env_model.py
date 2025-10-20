from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any, Union
from pathlib import Path

class Env(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
        populate_by_name=True
    )
    user_id: str = Field(default="anonymous")
    work_dir: Union[str, Path] = Field(default=".")
    # RunLogger 대신 Any (외부 주입)
    run_logger: Optional[Any] = None
    url: Optional[str] = None