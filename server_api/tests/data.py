import base64
import datetime
import quopri
from typing import List
from imapclient.response_types import Address, Envelope


class BodyPart(tuple):

    @classmethod
    def generate_part_with_line_number(cls, content_size, content_type, content_sub_type, content_type_parameters,
                                       content_transfer, content_line_number, content_disposition):
        return cls(
            (content_type, content_sub_type, content_type_parameters, None, None,
             content_transfer, content_size, content_line_number, None, content_disposition)
        )

    @classmethod
    def generate_part(cls, content_size, content_type, content_sub_type, content_type_parameters,
                      content_transfer, content_disposition, content_id=None):
        return cls(
            (content_type, content_sub_type, content_type_parameters, content_id, None,
             content_transfer, content_size, None, content_disposition)
        )

    @classmethod
    def generate_styled_part(cls):
        return cls.generate_part_with_line_number(
            10,
            b'text',
            b'html',
            (b'Charset', b'utf-8'),
            b'base64',
            1,
            None,
        )

    @classmethod
    def generate_quoted_styled_part(cls):
        return cls.generate_part_with_line_number(
            10,
            b'text',
            b'html',
            (b'Charset', b'utf-8'),
            b'quoted-printable',
            1,
            None,
        )

    @classmethod
    def generate_attachment_part(cls):
        return cls.generate_part(
            10,
            b'application',
            b'pdf',
            (b'name', b'report.pdf'),
            b'base64',
            (b'attachment', (b'filename', b'report.pdf', b'size', b'13264')),
        )

    @classmethod
    def generate_embedded_part(cls):
        return cls.generate_part(
            10,
            b'image',
            b'png',
            (b'name', b'report.pdf'),
            b'base64',
            (b'inline', (b'filename', b'report.pdf', b'size', b'13264')),
            b'id',
        )

    @classmethod
    def generate_attachment_missing_disposition_filename_part(cls):
        return cls.generate_part(
            10,
            b'application',
            b'pdf',
            (b'name', b'report.pdf'),
            b'base64',
            (b'attachment', (b'size', b'13264')),
        )

    @classmethod
    def generate_attachment_missing_filename_part(cls):
        return cls.generate_part(
            10,
            b'application',
            b'pdf',
            None,
            b'base64',
            (b'attachment', (b'size', b'13264')),
        )

    @classmethod
    def generate_attachment_without_name_part(cls):
        return cls.generate_part(
            10,
            b'application',
            b'pdf',
            None,
            b'base64',
            (b'attachment', (b'filename', b'report.pdf', b'size', b'13264')),
        )

    @classmethod
    def generate_text_part(cls):
        return cls.generate_part_with_line_number(
            10,
            b'text',
            b'plain',
            (b'Charset', b'utf-8'),
            b'7bit',
            1,
            None
        )

    @classmethod
    def generate_alternative_part(cls):
        return cls(([cls.generate_text_part(), cls.generate_styled_part()], (b'mixed', b'mixed')))

    @classmethod
    def generate_recursive_part(cls):
        return cls(([cls(([cls.generate_text_part(), cls.generate_text_part()], (b'mixed', b'mixed'))),
                     cls.generate_styled_part()], (b'mixed', b'mixed')))

    @classmethod
    def generate_quoted_alternative_part(cls):
        return cls(([cls.generate_text_part(), cls.generate_quoted_styled_part()], (b'mixed', b'mixed')))

    @classmethod
    def generate_attachment_alternative_part(cls):
        return cls(([cls.generate_text_part(), cls.generate_styled_part(), cls.generate_attachment_part()],
                    (b'mixed', b'mixed')))

    @classmethod
    def generate_with_embedded_part(cls):
        return cls(([cls.generate_text_part(), cls.generate_styled_part(), cls.generate_embedded_part()],
                    (b'mixed', b'mixed')))

    @classmethod
    def generate_attachment_without_name_alternative_part(cls):
        return cls(([cls.generate_text_part(), cls.generate_styled_part(), cls.generate_attachment_without_name_part()],
                    (b'mixed', b'mixed')))

    @property
    def is_multipart(self):
        return isinstance(self[0], list)


class MockedData:

    @classmethod
    def get_mailboxes(cls) -> list:
        return [(None, None, b'INBOX')]

    @classmethod
    def get_mailbox_status(cls) -> dict:
        return {
            b'MESSAGES': 1,
            b'UNSEEN': 1,
            b'RECENT': 1,
        }

    @classmethod
    def get_envelope(cls) -> Envelope:
        user_sample = {
            "name": None,
            "route": None,
            "mailbox": b'user1',
            "host": b'home.org'
        }

        user_with_sample = {
            "name": b'name',
            "route": None,
            "mailbox": b'user1',
            "host": b'home.org'
        }
        return Envelope(date=datetime.datetime(2021, 10, 21, 16, 0, 53),
                        subject=b'testing',
                        from_=(Address(**user_sample),),
                        sender=(Address(**user_sample),),
                        reply_to=(Address(**user_sample),),
                        to=(Address(**user_sample),),
                        cc=(Address(**user_with_sample),),
                        bcc=(Address(**user_sample),),
                        in_reply_to=None,
                        message_id=b'<aab3104f3e7433743fb58553960822d1@home.org>')

    @classmethod
    def _construct_headers(cls, headers: dict) -> bytes:
        headers_string = ""
        for name, value in headers.items():
            headers_string = headers_string + "%s: %s\r\n" % (name, value)
        headers_string = headers_string + "\r\n"
        return bytes(headers_string, "utf-8")

    @classmethod
    def get_headers(cls) -> bytes:
        headers = {
            'Content-Type': 'text/plain; charset="utf-8"',
            'Date': 'Tue, 24 May 2022 07:07:38 +0000'
        }
        return cls._construct_headers(headers)

    @classmethod
    def get_fetch_return_value(cls) -> dict:
        return {1: {
            b'ENVELOPE': MockedData.get_envelope(),
            b'BODY[HEADER.FIELDS (X-PRIORITY IMPORTANCE)]': b'\r\n',
            b'UID': 1,
            b'FLAGS': [b'\\Seen'],
            b'BODY[1]': b'test message',
            b'BODY[1]<0>': b'test message',
            b'BODYSTRUCTURE': BodyPart.generate_text_part(),
            b'BODY[HEADER]': cls.get_headers()
        }}

    @classmethod
    def get_fetch_with_priority_return_value(cls) -> dict:
        return {1: {
            b'ENVELOPE': MockedData.get_envelope(),
            b'BODY[HEADER.FIELDS (X-PRIORITY IMPORTANCE)]': b'Importance: low\r\nX-Priority: 5\r\n\r\n',
            b'UID': 1,
            b'FLAGS': [b'\\Seen'],
            b'BODY[1]': b'test message',
            b'BODY[1]<0>': b'test message',
            b'BODYSTRUCTURE': BodyPart.generate_text_part(),
            b'BODY[HEADER]': cls.get_headers()
        }}

    @classmethod
    def get_peek_return_value(cls) -> dict:
        return {1: {
            b'ENVELOPE': MockedData.get_envelope(),
            b'BODY[HEADER.FIELDS (X-PRIORITY IMPORTANCE)]': b'\r\n',
            b'SEQ': 1,
            b'FLAGS': [b'\\Seen'],
            b'BODY[1]': b'test message',
            b'BODY[1]<0>': b'test message',
            b'BODYSTRUCTURE': BodyPart.generate_text_part(),
            b'BODY[HEADER]': cls.get_headers()
        }}

    @classmethod
    def get_fetch_recursive_return_value(cls) -> dict:
        return {1: {
            b'ENVELOPE': MockedData.get_envelope(),
            b'UID': 1,
            b'FLAGS': [b'\\Seen'],
            b'BODY[1]': b'test message',
            b'BODY[1.1]': b'test message',
            b'BODY[2]': base64.b64encode(b'<p> test message </p>'),
            b'BODY[1]<0>': b'test message',
            b'BODYSTRUCTURE': BodyPart.generate_recursive_part(),
            b'BODY[HEADER]': cls.get_headers()
        }}

    @classmethod
    def get_fetch_with_arabic_subject_return_value(cls) -> dict:
        return {1: {
            b'ENVELOPE': MockedData.get_envelope(),
            b'UID': 1,
            b'FLAGS': [b'\\Seen'],
            b'BODY[1]': b'test message',
            b'BODY[1]<0>': b'test message',
            b'BODYSTRUCTURE': BodyPart.generate_text_part(),
            b'BODY[HEADER]': b'Content-Type: text/plain\r\nSubject: =?utf-8?b?2LnZhtmI2KfZhg==?=\r\n\r\n'
        }}

    @classmethod
    def get_fetch_with_styled_body_return_value(cls) -> dict:
        return {1: {
            b'ENVELOPE': MockedData.get_envelope(),
            b'UID': 1,
            b'FLAGS': [b'\\Seen'],
            b'BODY[1]': b'test message',
            b'BODY[2]': base64.b64encode(b'<p> test message </p>'),
            b'BODYSTRUCTURE': BodyPart.generate_alternative_part(),
            b'BODY[HEADER]': cls.get_headers()
        }}

    @classmethod
    def get_fetch_with_only_styled_body_return_value(cls) -> dict:
        return {1: {
            b'ENVELOPE': MockedData.get_envelope(),
            b'UID': 1,
            b'FLAGS': [b'\\Seen'],
            b'BODY[1]': base64.b64encode(b'<p> test message </p>'),
            b'BODY[1]<0>': base64.b64encode(b'<p> test message </p>'),
            b'BODYSTRUCTURE': BodyPart.generate_styled_part(),
            b'BODY[HEADER]': cls.get_headers()
        }}

    @classmethod
    def get_fetch_with_quoted_styled_body_return_value(cls) -> dict:
        return {1: {
            b'ENVELOPE': MockedData.get_envelope(),
            b'UID': 1,
            b'FLAGS': [b'\\Seen'],
            b'BODY[1]': b'test message',
            b'BODY[2]': quopri.encodestring(bytes("<p> عنوان </p>", "utf-8")),
            b'BODYSTRUCTURE': BodyPart.generate_quoted_alternative_part(),
            b'BODY[HEADER]': cls.get_headers()
        }}

    @classmethod
    def get_fetch_with_attachment_return_value(cls) -> dict:
        return {1: {
            b'ENVELOPE': MockedData.get_envelope(),
            b'UID': 1,
            b'FLAGS': [b'\\Seen'],
            b'BODY[1]': b'test message',
            b'BODY[2]': base64.b64encode(b'<p> test message </p>'),
            b'BODYSTRUCTURE': BodyPart.generate_attachment_alternative_part(),
            b'BODY[HEADER]': cls.get_headers()
        }}

    @classmethod
    def get_fetch_with_embedded_image_return_value(cls) -> dict:
        return {1: {
            b'ENVELOPE': MockedData.get_envelope(),
            b'UID': 1,
            b'FLAGS': [b'\\Seen'],
            b'BODY[1]': b'test message',
            b'BODY[2]': base64.b64encode(b'<p> test message </p>'),
            b'BODY[3]': base64.b64encode(b'<p> test message </p>'),
            b'BODYSTRUCTURE': BodyPart.generate_with_embedded_part(),
            b'BODY[HEADER]': cls.get_headers()
        }}

    @classmethod
    def get_fetch_with_attachment_without_name_return_value(cls) -> dict:
        return {1: {
            b'ENVELOPE': MockedData.get_envelope(),
            b'UID': 1,
            b'FLAGS': [b'\\Seen'],
            b'BODY[1]': b'test message',
            b'BODY[2]': base64.b64encode(b'<p> test message </p>'),
            b'BODYSTRUCTURE': BodyPart.generate_attachment_without_name_alternative_part(),
            b'BODY[HEADER]': cls.get_headers()
        }}

    @classmethod
    def get_select_folder_return_value(cls, exists: int):
        return {b'EXISTS': exists}

    @classmethod
    def get_fetch_attachment(cls):
        content_encoding = b'Content-Transfer-Encoding: base64\r\n'
        content_type = b'Content-Type: application/pdf;\r\n name=blank.pdf\r\n'
        content_disposition = b'Content-Disposition: attachment;\r\n filename=blank.pdf;\r\n size=19741\r\n\r\n'
        return {
            1: {
                bytes("BODY[1]", "utf-8"): b'aGVsbG8K',
                bytes("BODY[1.MIME]", "utf-8"): content_encoding + content_type + content_disposition,
                b'BODYSTRUCTURE': BodyPart.generate_attachment_part(),
            }
        }

    @classmethod
    def get_fetch_attachment_with_disposition_filename_messing(cls):
        data = cls.get_fetch_attachment()
        data[1][b'BODYSTRUCTURE'] = BodyPart.generate_attachment_missing_disposition_filename_part()
        return data

    @classmethod
    def get_fetch_attachment_with_filename_messing(cls):
        data = cls.get_fetch_attachment()
        data[1][b'BODYSTRUCTURE'] = BodyPart.generate_attachment_missing_filename_part()
        return data


class Arguments:

    USER1_SAMPLE_NAME = "user1@home.org"
    USER2_SAMPLE_NAME = "user2@home.org"
    BODY_SAMPLE = "some sample"
    STYLED_BODY_SAMPLE = "<p> some sample </p>"
    SUBJECT_SAMPLE = "some subject"

    @classmethod
    def get_create_mailbox_arguments(cls) -> dict:
        return {"mailbox": "myfolder"}

    @classmethod
    def get_delete_mailbox_arguments(cls) -> dict:
        return {"mailbox": "myfolder"}

    @classmethod
    def get_delete_default_mailbox_arguments(cls) -> dict:
        return {"mailbox": "INBOX"}

    @classmethod
    def get_rename_mailbox_arguments(cls) -> dict:
        return {
            "mailbox": "myfolder",
            "new_mailbox": "myNewFolder"
        }

    @classmethod
    def get_rename_default_mailbox_arguments(cls) -> dict:
        return {
            "mailbox": "INBOX",
            "new_mailbox": "myNewFolder"
        }

    @classmethod
    def get_list_mail_arguments(cls, search_query: List = None) -> dict:
        args = {
            "mailbox": "INBOX",
            "page": 1,
            "limit": 10
        }
        if search_query:
            args["search_query"] = search_query
        return args

    @classmethod
    def get_fetch_mail_arguments(cls) -> dict:
        return {
            "mailbox": "INBOX",
            "mail_uid": 1
        }

    @classmethod
    def get_send_email_arguments(cls) -> dict:
        return {
            "recipients": [cls.USER1_SAMPLE_NAME, cls.USER2_SAMPLE_NAME],
            "body": cls.BODY_SAMPLE,
            "headers": [
                {"name": "To", "value": cls.USER1_SAMPLE_NAME},
                {"name": "Subject", "value": cls.SUBJECT_SAMPLE}
            ]
        }

    @classmethod
    def get_send_email_with_styled_body_arguments(cls) -> dict:
        return {
            "recipients": [cls.USER1_SAMPLE_NAME, cls.USER2_SAMPLE_NAME],
            "body": cls.BODY_SAMPLE,
            "styled_body": cls.STYLED_BODY_SAMPLE,
            "headers": [
                {"name": "To", "value": cls.USER1_SAMPLE_NAME},
                {"name": "Subject", "value": cls.SUBJECT_SAMPLE}
            ]
        }

    @classmethod
    def get_send_email_wit_attachment_arguments(cls) -> dict:
        return {
            "recipients": [cls.USER1_SAMPLE_NAME, cls.USER2_SAMPLE_NAME],
            "body": cls.BODY_SAMPLE,
            "headers": [
                {"name": "To", "value": cls.USER1_SAMPLE_NAME},
                {"name": "Subject", "value": cls.SUBJECT_SAMPLE}
            ],
            "attachments": [
                {
                    "content": "content one",
                    "content_type": "application/pdf",
                    "content_name": "some_file.pdf",
                    "content_size": 8900
                }
            ]
        }

    @classmethod
    def get_send_email_wit_attachment_content_id_arguments(cls) -> dict:
        return {
            "recipients": [cls.USER1_SAMPLE_NAME, cls.USER2_SAMPLE_NAME],
            "body": cls.BODY_SAMPLE,
            "headers": [
                {"name": "To", "value": cls.USER1_SAMPLE_NAME},
                {"name": "Subject", "value": cls.SUBJECT_SAMPLE}
            ],
            "attachments": [
                {
                    "content": "content one",
                    "content_type": "application/pdf",
                    "content_name": "some_file.pdf",
                    "content_id": "0d92b464-74e3-4dd4-bbf6-15005232830f",
                    "content_size": 8900
                }
            ]
        }

    @classmethod
    def get_append_mail_arguments(cls) -> dict:
        return {
            "mailbox": "INBOX",
            "body": cls.BODY_SAMPLE,
            "headers": [
                {"name": "To", "value": cls.USER1_SAMPLE_NAME},
                {"name": "Subject", "value": cls.SUBJECT_SAMPLE}
            ]
        }

    @classmethod
    def get_copy_mail_arguments(cls) -> dict:
        return {
            "mailbox": "INBOX",
            "mail_uid": [1, 2],
            "target_mailbox": "Deleted"
        }

    @classmethod
    def get_delete_mail_arguments(cls) -> dict:
        return {
            "mailbox": "INBOX",
            "mail_uid": [1, 2]
        }

    @classmethod
    def get_delete_all_mail_arguments(cls) -> dict:
        return {
            "mailbox": "INBOX",
            "mail_uid": []
        }

    @classmethod
    def get_flags_arguments(cls) -> dict:
        return {
            "mailbox": "Inbox",
            "mail_uid": [1],
            "flags": ["\\seen", "\\Answered"]
        }
