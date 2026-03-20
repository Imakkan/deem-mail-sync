from common.utils import construct_mail_message, deconstruct_mail_message
from typing import Tuple
from base64 import b64decode


def construct_sieve_mime_body(body, styled_body):
    message = construct_mail_message(body, styled_body, [], []).as_string()
    sieve_mime_body = message.replace('"', '\\"')
    return sieve_mime_body


def deconstruct_sieve_mime_body(sieve_mime_body: str) -> Tuple[str, str]:
    body = ""
    styled_body = ""
    message = sieve_mime_body.replace('\\"', '"').replace('\\n', '\\r\\n')[1:-1]
    mail_message = deconstruct_mail_message(message)
    mail_message.get_content_type()
    for part in mail_message.get_payload():
        content_type = part.get_content_type()
        if content_type == "text/plain":
            body = part.get_payload()
        elif content_type == "text/html":
            styled_body = b64decode(part.get_payload()).decode()
    return body, styled_body
