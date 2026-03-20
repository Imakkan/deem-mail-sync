from typing import Optional, List
from pydantic import BaseModel


class PutAutoreplyScript(BaseModel):
    subject: str
    body: str
    styled_body: Optional[str]


class PutScript(BaseModel):
    rules: List[dict]
