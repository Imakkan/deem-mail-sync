from pydantic import BaseModel
from typing import Optional, List


class ListMail(BaseModel):
    mailbox: str
    page: int
    limit: int
    search_query: Optional[List]
    reverse: Optional[bool]


class CreateMailbox(BaseModel):
    mailbox: str


class RenameMailbox(BaseModel):
    mailbox: str
    new_mailbox: str


class DeleteMailbox(CreateMailbox):
    pass


class FetchMail(BaseModel):
    mailbox: str
    mail_uid: int


class PeekMail(BaseModel):
    mailbox: str
    mail_uid: int


class DownloadAttachment(BaseModel):
    mailbox: str
    mail_uid: int
    part_number: str


class AppendMail(BaseModel):
    body: str
    styled_body: Optional[str]
    headers: List[dict]
    attachments: Optional[List[dict]]
    mailbox: str


class CopyMail(BaseModel):
    mailbox: str
    mail_uid: List[str]
    target_mailbox: str


class DeleteMail(BaseModel):
    mailbox: str
    mail_uid: List[str]


class Flags(BaseModel):
    mailbox: str
    mail_uid: List[int]
    flags: List[str]
