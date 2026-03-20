import base64
import quopri
import math
import re

from tnefparse import TNEF, TNEFAttachment
from urllib import parse as url_parser

from dateutil import parser

from imapclient.response_types import BodyData
from email.header import decode_header
from typing import List, Callable, Union


class MailPager:

    def __init__(self, page: int, limit: int, total: int):
        self.page = page
        self.limit = limit
        self.total = total
        self.start_boundary = (self.page - 1) * self.limit
        self.end_boundary = self.start_boundary + self.limit
        self.pages = math.ceil(self.total / self.limit) if self.total > 0 else 1

    def get_as_search_seq(self, search_result: List) -> List:
        return search_result[self.start_boundary: self.end_boundary]


class MailParser:
    SKIP_HEADER = ["Content-Transfer-Encoding"]

    @classmethod
    def _prepare_header(cls, body: str) -> str:
        body = body[:len(body) - 4]
        body = body.replace("\r\n\t", " ")
        body = body.replace("\r\n ", " ")
        return body

    @classmethod
    def decode_header_value(cls, header_value: str) -> str:
        decoded_header_value = ''
        for value, charsets in decode_header(header_value):
            if type(value) == str:
                decoded_value = value
                if decoded_value.startswith('utf-8'):
                    decoded_value = url_parser.unquote(decoded_value[7:])
            else:
                decoded_value = value.decode() if charsets is None else value.decode(charsets)
            decoded_header_value = decoded_header_value + decoded_value
        return decoded_header_value

    @classmethod
    def pars_date_header(cls, header_value: str) -> int:
        try:
            return int(parser.parse(header_value).timestamp())
        except Exception as s:
            match_result = re.search(r'(.*)(\(.*\))', header_value)
            return int(parser.parse(match_result.groups()[0]).timestamp())

    @classmethod
    def construct_header(cls, header: List[str]) -> dict:
        name = header[0]
        value = cls.decode_header_value(header[1]) if len(header) == 2 else ""

        if value and name == "Date":
            value = cls.pars_date_header(value)
        return {"name": name, "value": value}

    @classmethod
    def parse_header(cls, body: str) -> List[dict]:
        headers = []
        body = cls._prepare_header(body)
        for message in body.split("\r\n"):
            if message:
                header = message.split(": ", 1)
                headers.append(cls.construct_header(header))
        return headers

    @classmethod
    def parse_priority_header(cls, body: str) -> dict:
        priority_headers = {"priority_name": "", "priority_value": ""}
        for header in cls.parse_header(body):
            if header.get("name") == "Importance":
                priority_headers["priority_name"] = header.get("value")
            if header.get("name") == "X-Priority":
                priority_headers["priority_value"] = header.get("value")
        return priority_headers


class MailBodyPart:
    EXCEPTION_ATTACHMENT_TYPE_ONLY = ["message/rfc822", "text/calendar"]
    DEFAULT_FILE_NAME = "attachment"
    DEFAULT_FILE_EXTENSION = "mime"
    CONTENT_TYPE_TYPE = 0
    CONTENT_TYPE_SUBTYPE = 1
    CONTENT_TYPE_PARAMETERS = 2
    CONTENT_ID = 3
    CONTENT_DESCRIPTION = 4
    CONTENT_TRANSFER_ENCODING = 5
    CONTENT_SIZE = 6
    CONTENT_NUMBER_OF_LINES = 7
    CONTENT_PARAMETER = 8
    CONTENT_DISPOSITION = 9
    CONTENT_LOCATION = 10
    CONTENT_LANGUAGE_CODE = 11

    def __init__(self, body_structure: BodyData, part_number: str):
        extension_data_offset = self._get_extension_data_offset(body_structure)
        self.charset = 'utf-8'
        self.part_number = part_number
        self.size = body_structure[self.CONTENT_SIZE]
        self.part_id = re.sub("[<>]", "", body_structure[self.CONTENT_ID].decode()) if body_structure[self.CONTENT_ID] else None
        self.type = self._parse_type(body_structure)
        self.type_parameters = self._parse_type_parameters(body_structure)
        self.transfer_encoding = self._parse_transfer_encoding(body_structure)
        self.disposition = None
        self.embedded_attachment = []
        self.disposition_parameters = []
        if self.type not in self.EXCEPTION_ATTACHMENT_TYPE_ONLY:
            self.disposition = body_structure[self.CONTENT_DISPOSITION - extension_data_offset]
            self.disposition_parameters = self._parse_disposition_parameters()

    def _get_extension_data_offset(self, body_structure: BodyData):
        return 0 if body_structure[self.CONTENT_TYPE_TYPE].decode().upper() == "text".upper() else 1

    def _parse_type(self, body_structure):
        return "%s/%s" % (
            body_structure[self.CONTENT_TYPE_TYPE].decode(), body_structure[self.CONTENT_TYPE_SUBTYPE].decode())

    def _parse_transfer_encoding(self, body_structure):
        return body_structure[self.CONTENT_TRANSFER_ENCODING].decode()

    def _parse_type_parameters(self, body_structure):
        parameters = []
        structure_parameters = body_structure[self.CONTENT_TYPE_PARAMETERS]
        if structure_parameters is not None:
            for i in range(0, len(structure_parameters), 2):
                key = structure_parameters[i].decode()
                value = structure_parameters[i + 1].decode()
                parameters.append({"key": key, "value": value})
                if key.lower() == 'charset':
                    self.charset = value
        return parameters

    def _has_disposition_parameters(self) -> bool:
        return self.disposition is not None and self.disposition[1] is not None and len(self.disposition) > 1

    def _parse_disposition_parameters(self):
        parameters = []
        structure_parameters = self.disposition[1] if self._has_disposition_parameters() else []
        for i in range(0, len(structure_parameters), 2):
            key = structure_parameters[i].decode()
            value = structure_parameters[i + 1].decode()
            parameters.append({"key": key, "value": value})
        return parameters

    def _get_file_name_from_disposition(self):
        filename = ""
        for parameter in self.disposition_parameters:
            if parameter["key"] in ["filename", "filename*"]:
                filename = parameter["value"]
                break
        return filename

    def _get_file_name_from_type(self):
        filename = ""
        for parameter in self.type_parameters:
            if parameter["key"] == "name":
                filename = parameter["value"]
                break
        return filename

    # TODO make the function more dynamic based on the content type
    def _generate_file_name(self):
        return "%s.%s" % (self.DEFAULT_FILE_NAME, self.DEFAULT_FILE_EXTENSION)

    def get_charset(self):
        return 'utf-8' if self.charset in ['ascii', 'us-ascii'] or not self.charset else self.charset

    def is_embedded(self) -> bool:
        return self.part_id is not None

    def is_attachment(self) -> bool:
        return (self.disposition is not None and self.disposition[0] == b'attachment') \
            or self.type in self.EXCEPTION_ATTACHMENT_TYPE_ONLY

    def get_attachment_name(self, encoded: bool = False) -> str:
        filename = self._get_file_name_from_disposition()
        if filename == "":
            filename = self._get_file_name_from_type()
        if filename == "":
            filename = self._generate_file_name()
        filename = MailParser.decode_header_value(filename)
        return url_parser.quote(filename) if encoded else filename

    def get_attachment_data_as_dict(self) -> dict:
        return {
            "part_number": self.part_number,
            "content_type": self.type,
            "content_name": self.get_attachment_name(),
            "content_size": self.size,
        }

    def get_attachment_mime_headers(self):
        headers = dict()
        if self.is_attachment():
            headers["Content-Type"] = self.type
            headers["Content-Disposition"] = "attachment; filename=%s" % self.get_attachment_name(encoded=True)
        return headers

    def get_fetch_query(self) -> str:
        return "BODY[%s]" % self.part_number

    def get_fetch_query_as_bytes(self) -> bytes:
        return bytes(self.get_fetch_query(), "utf-8")

    def is_tnef_encoded(self) -> bool:
        # TODO refactor to be a list of tnef
        return self.type in ["application/ms-tnef", "application/vnd.ms-tnef"]

    def is_binary_encoded(self) -> bool:
        return self.transfer_encoding in ["7bit", "8bit", "binary"]

    def is_base64_encoded(self) -> bool:
        return self.transfer_encoding.lower() == "base64"

    def is_quoted_printable_encoded(self) -> bool:
        return self.transfer_encoding.lower() == "quoted-printable"

    def decode_message(self, message: bytes) -> str:
        return self.get_byte_decoder()(message).decode(self.get_charset())

    def decode_tnef_message(self, message: bytes) -> tuple:
        return self.decode_tnef(self.get_byte_decoder()(message))

    def get_byte_decoder(self):
        if self.is_binary_encoded():
            return lambda x: x
        if self.is_base64_encoded():
            return lambda x: base64.b64decode(x)
        if self.is_quoted_printable_encoded():
            return lambda x: quopri.decodestring(x)

    def decode_tnef(self, body):
        tnef_obj = TNEF(body)
        return tnef_obj.htmlbody, [self.decode_tnef_attachments(index, attachment) for index, attachment in enumerate(tnef_obj.attachments)]

    def decode_tnef_attachments(self, index: int, tnef_attachment: TNEFAttachment):
        content_extinsions, content_type, content_id = self.decode_tnef_attachemnt_meta_info(tnef_attachment)
        return {
            "part_number": "%s.%s" % (self.part_number, index),
            "content_type": content_type,
            "content_name": tnef_attachment.long_filename(),
            "content_size": len(tnef_attachment.data),
            "content_id": content_id,
            "content": tnef_attachment.data
        }

    def decode_tnef_attachemnt_meta_info(self, tnef_attachment: TNEFAttachment):
        attachment_extension = ".bin"
        attachment_type = "application/octect-stream"
        attachment_id = ""
        for mapi_attribute in tnef_attachment.mapi_attrs:
            if mapi_attribute.name_str == 'MAPI_ATTACH_EXTENSION':
                attachment_extension = mapi_attribute.data
            if mapi_attribute.name_str == 'MAPI_ATTACH_MIME_TAG':
                attachment_type = mapi_attribute.data
            if mapi_attribute.name_str == 'MAPI_ATTACH_CONTENT_ID':
                attachment_id = mapi_attribute.data
        return attachment_extension, attachment_type, attachment_id


class MailBodyParts:
    MAIN_TEXT_TYPE = "text/plain"
    MAIN_HTML_TYPE = "text/html"
    MAIN_TYPE = [MAIN_HTML_TYPE, MAIN_TEXT_TYPE]

    def __init__(self, body: BodyData):
        self.plain_content_parts = []
        self.html_content_parts = []
        self.embedded_parts = []
        self.attachment_parts = []
        self.tnef_content_parts = []
        if body.is_multipart:
            self._construct_parts(body[0])
        else:
            self._construct_part(body, "1")

    def _append_main_part(self, body_part: MailBodyPart):
        if body_part.type == self.MAIN_HTML_TYPE:
            self.html_content_parts.append(body_part)
        elif body_part.type == self.MAIN_TEXT_TYPE:
            self.plain_content_parts.append(body_part)

    @classmethod
    def _append_part(cls, parent: str, part: int) -> str:
        return "%s" % part if parent == "" else "%s.%s" % (parent, part)

    def _construct_part(self, part: BodyData, part_number: str):
        body_part = MailBodyPart(part, part_number)
        if body_part.is_embedded() and body_part.type not in self.MAIN_TYPE:
            self.embedded_parts.append(body_part)
        elif body_part.is_tnef_encoded():
            self.tnef_content_parts.append(body_part)
        elif body_part.is_attachment():
            self.attachment_parts.append(body_part)
        else:
            self._append_main_part(body_part)

    def _construct_parts(self, parts: Union[List[BodyData], BodyData], parent_number=""):
        part_number = 1
        for part in parts:
            if part.is_multipart:
                self._construct_parts(part[0], self._append_part(parent_number, part_number))
            else:
                self._construct_part(part, self._append_part(parent_number, part_number))
            part_number += 1

    def get_attachment_parts(self) -> List[MailBodyPart]:
        return self.attachment_parts

    def get_attachment_part(self, part_number: str) -> MailBodyPart:
        for part in self.attachment_parts:
            if part.part_number == part_number:
                return part

    def get_embedded_parts(self) -> List[MailBodyPart]:
        return self.embedded_parts

    def get_styled_part(self) -> MailBodyPart:
        if self.has_html_part():
            return self.html_content_parts[0]
        if self.has_tnef_part():
            return self.tnef_content_parts[0]

    def get_plain_part(self) -> MailBodyPart:
        if self.has_plain_part():
            return self.plain_content_parts[0]

    def get_tnef_part(self) -> MailBodyPart:
        if self.has_tnef_part():
            return self.tnef_content_parts[0]

    def has_embedded_parts(self) -> bool:
        if len(self.embedded_parts):
            return True
        return False

    def has_html_part(self) -> bool:
        if len(self.html_content_parts):
            return True
        return False

    def has_styled_part(self) -> bool:
        return self.has_tnef_part() or self.has_html_part()

    def has_tnef_part(self) -> bool:
        if len(self.tnef_content_parts):
            return True
        return False

    def has_plain_part(self) -> bool:
        if len(self.plain_content_parts):
            return True
        return False
