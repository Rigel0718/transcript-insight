from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any, Union
from pathlib import Path
from app.core.logger import NoopRunLogger, RunLoggerLike

class Env(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
        populate_by_name=True
    )
    user_id: str = Field(default="anonymous")
    work_dir: Union[str, Path] = Field(default=".")
    run_logger: RunLoggerLike = Field(default_factory=NoopRunLogger)
    url: Optional[str] = None