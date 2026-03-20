from typing import List, Dict
from email.message import EmailMessage, Message
from email.header import Header
from email.mime.application import MIMEApplication
from email.parser import BytesParser

parser = BytesParser()


def construct_mail_message(body: str, styled_body: str, headers: List[dict], attachments: List[dict]) -> EmailMessage:

    message = EmailMessage()
    message.set_content(body)
    message.replace_header("Content-Type", "text/plain; charset=utf-8")

    for header in headers:
        message.add_header(header["name"], _encode_header(header["value"]).replace("\n", ""))

    if styled_body:
        message.add_alternative(bytes(styled_body, "utf-8"), maintype='text', subtype='html')

    if attachments:
        message.make_mixed()
        for attachment in attachments:
            message.attach(_construct_attachment(
                attachment["content"],
                attachment["content_type"],
                attachment["content_name"],
                attachment["content_size"],
                attachment.get("content_id"),
                attachment.get("is_disposition", True),
                attachment.get("content_param", dict())
            ))

    return message


def deconstruct_mail_message(message: str) -> Message:
    return parser.parsebytes(bytes(message, "utf-8"))


def _construct_attachment(content: str, content_type: str, content_name: str, content_size: int,
                          content_id: str = None, is_disposition: bool = True, content_params: Dict = None):
    attachment_message = MIMEApplication(bytes(content, "utf-8"), _encoder=lambda x: x)
    attachment_message.replace_header(
        "Content-Type",
        _construct_content_type(content_type, content_name, content_params))
    if is_disposition:
        attachment_message.add_header("Content-Disposition", _construct_content_disposition(content_name, content_size))
    attachment_message.add_header("Content-Transfer-Encoding", "base64")
    if content_id is not None:
        attachment_message.add_header("Content-Id", content_id)
    return attachment_message


def _construct_content_type_params(content_params: dict) -> str:
    params_string = ""
    for param in content_params:
        params_string = "%s%s" % (
            params_string,
            ';\n %s=%s' % (_encode_header(param), _encode_header(content_params[param])))
    return params_string


def _construct_content_type(content_type, content_name, content_params):
    content = '%s;\n name="%s"' % (content_type, _encode_header(content_name))
    return "%s%s" % (content, _construct_content_type_params(content_params))


def _construct_content_disposition(content_name, content_size):
    return 'attachment;\n filename="%s";\n size="%s"' % (_encode_header(content_name), content_size)


def _encode_header(header_value: str) -> str:
    return header_value if header_value.isascii() else Header(header_value, "utf-8").encode()
