from __future__ import annotations
from typing import List, Dict, Optional
from pydantic import BaseModel


class Element(BaseModel):
    category: str  # upstage-doc-parser categories : table, figure, chart, heading1, header, footer, caption, paragraph, equation, list, index, footnote
    content: str = ""
    markdown: str = ""
    base64_encoding: Optional[str] = None
    id: Optional[int] = None
    coordinates: Optional[List[Dict]] = None

    def copy(self) -> Element:
        return self.model_copy(deep=True)