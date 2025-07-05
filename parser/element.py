from __future__ import annotations
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


class Element(BaseModel):
    category: str  # upstage-doc-parser categories : table, figure, chart, heading1, header, footer, caption, paragraph, equation, list, index, footnote
    content: str = ""
    markdown: str = ""
    base64_encoding: Optional[str] = None
    id: Optional[int] = None
    ocr_need : bool = False

    def copy(self) -> Element:
        return self.model_copy(deep=True)


class OCRElement(BaseModel):
    id: int = Field(..., description="Unique ID of the OCR element.")
    vertices : Dict[str, int] = Field(..., description='{x : ..., y : ... } Top-left coordinate of the OCR element.')
    text : str = Field(..., description='Recognized text content from the OCR element.')

    def copy(self) -> OCRElement:
        return self.model_copy(deep=True)


class TableBoundary(BaseModel):
    y_top : int = Field(description='Top Y-position of the grade table section.')
    y_bottom : int = Field(description='Bottom Y-position that marks the end of the grade table section.')

class CheckParsedResult(BaseModel):
    decision: Literal["YES", "NO"] = Field(..., description=(
            'Return **"YES"** if the parsed output is NOT sufficiently structured '
            'and therefore needs additional OCR processing. '
            'Return **"NO"** if the structure is good enough for an LLM to understand '
            'without further parsing.'
        ))