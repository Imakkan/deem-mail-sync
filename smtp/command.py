from typing import List
from smtplib import SMTP
from .decorators import raise_command_exception
from common import utils


class Command:

    @classmethod
    @raise_command_exception
    def send_email(cls,
                   session: SMTP,
                   recipients: List[str],
                   body: str,
                   headers: List[dict],
                   attachments: List[dict],
                   styled_body: str = None,
                   ) -> None:

        message = utils.construct_mail_message(body, styled_body, headers, attachments)
        from_address = "%s <%s>" % (session.user.get("name", ""), session.user.get("email"))
        message.add_header("From", from_address)

        session.send_message(msg=message, from_addr=from_address, to_addrs=recipients)
