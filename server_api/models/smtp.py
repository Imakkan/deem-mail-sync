from pydantic import BaseModel
from typing import List, Optional


class SendMail(BaseModel):
    recipients: List[str]
    body: str
    styled_body: Optional[str]
    headers: List[dict]
    attachments: Optional[List[dict]]
