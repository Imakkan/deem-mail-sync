from typing import Dict

from pydantic import BaseModel
from server_api.api.enumerate import Command


class MailCommand(BaseModel):
    command: Command
    arguments: Dict
