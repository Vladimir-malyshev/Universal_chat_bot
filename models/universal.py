from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class Attachment(BaseModel):
    type: Literal['audio', 'image']
    url: Optional[str] = None
    file_path: Optional[str] = None

class UniversalMessage(BaseModel):
    channel: str
    user_id: str
    text: Optional[str] = None
    attachments: List[Attachment] = Field(default_factory=list)
