import base64
import re
from datetime import datetime, timedelta
import os

from typing import List
from imapclient import IMAPClient
from imapclient.response_types import Address
from .utils import MailPager, MailParser, MailBodyParts, MailBodyPart
from .decorators import raise_command_exception, specified_uid_or_all
from common import utils
from .exceptions import RenameDefaultMailboxException, DeleteDefaultMailboxException
from urllib import parse as url_parser


class Command:

    DEFAULT_SEARCH_DATE_DELTA = 30 * int(os.environ.get("DATE_TIME_DELTA", 6))
    DEFAULT_SEARCH_MAIL_CRITERIA = "ALL"
    DEFAULT_SORT_MAIL_CRITERIA = ["REVERSE DATE"]
    DEFAULT_MAILBOXES = ["INBOX", "Sent", "Deleted", "Drafts", "inbox"]
    MISSING_ADDRESS_VALUES = ["SYNTAX_ERROR", "MISSING_DOMAIN", "MISSING_MAILBOX"]

    @classmethod
    @raise_command_exception
    def list_mail_boxes(cls, imap_session: IMAPClient):
        mail_boxes = imap_session.list_folders()
        mail_boxes_with_status = []
        for mail_box in mail_boxes:
            box = dict()
            # TODO some folder after delete show in list of folders
            try:
                status = imap_session.folder_status(mail_box[2])
            except Exception:
                continue
            box["name"] = mail_box[2]
            box["messages"] = status[b'MESSAGES']
            box["unseen"] = status[b'UNSEEN']
            box["recent"] = status[b'RECENT']
            mail_boxes_with_status.append(box)
        return mail_boxes_with_status

    @classmethod
    @raise_command_exception
    def create_mail_box(cls, imap_session: IMAPClient, mailbox: str):
        imap_session.create_folder(mailbox)
        imap_session.subscribe_folder(mailbox)

    @classmethod
    @raise_command_exception
    def rename_mail_box(cls, imap_session: IMAPClient, mailbox: str, new_mailbox: str):
        if mailbox in cls.DEFAULT_MAILBOXES:
            raise RenameDefaultMailboxException("invalid mailbox name, can not rename default mailbox: %s" % mailbox)
        imap_session.rename_folder(mailbox, new_mailbox)

    @classmethod
    @raise_command_exception
    def delete_mail_box(cls, imap_session: IMAPClient, mailbox: str):
        if mailbox in cls.DEFAULT_MAILBOXES:
            raise DeleteDefaultMailboxException("invalid mailbox name, can not delete default mailbox: %s" % mailbox)
        imap_session.unsubscribe_folder(mailbox)
        imap_session.delete_folder(mailbox)

    @classmethod
    @raise_command_exception
    def list_mails(cls, imap_session: IMAPClient, mailbox: str, page: int,
                   limit: int, search_query: List, reverse: bool) -> dict:
        mailbox_exist = imap_session.select_folder(mailbox)
        if not mailbox_exist[b'EXISTS']:
            return cls._get_paged_response(MailPager(page, limit, 0), [])

        query = ["ENVELOPE", "FLAGS", "UID", "BODYSTRUCTURE",
                 "BODY.PEEK[HEADER.FIELDS (X-Priority Importance)]", "BODY.PEEK[1]<0.35>"]

        result = cls.search_mails(imap_session, reverse, cls._get_default_search(search_query, imap_session))
        pager = MailPager(page, limit, len(result))
        paged_result = [
            cls._construct_envelope(data) for _, data in imap_session.fetch(
                pager.get_as_search_seq(result), query).items()
        ]

        return cls._get_paged_response(pager, paged_result)

    @classmethod
    @raise_command_exception
    def peek_mail(cls, imap_session: IMAPClient, mailbox: str, mail_uid: int) -> dict:
        imap_session.select_folder(mailbox)
        imap_session.use_uid = True
        query = ["ENVELOPE", "FLAGS", "UID", "BODYSTRUCTURE", "BODY.PEEK[HEADER.FIELDS (X-Priority Importance)]",
                 "BODY.PEEK[1]<0.25>"]

        data = imap_session.fetch(mail_uid, query)[mail_uid]
        data[b'UID'] = mail_uid
        return cls._construct_envelope(data)

    @classmethod
    @raise_command_exception
    def search_mails(cls, imap_session: IMAPClient, reverse: bool, search_criteria) -> list:

        sort_criteria = ["X-SCORE", "DATE"] if reverse else ["X-SCORE", "REVERSE", "DATE"]
        search_criteria = search_criteria if search_criteria else cls.DEFAULT_SEARCH_MAIL_CRITERIA

        result = imap_session.sort(sort_criteria, search_criteria)
        return result

    @classmethod
    @raise_command_exception
    def fetch_mail(cls, imap_session: IMAPClient, mailbox: str, mail_uid: int) -> dict:
        mail_uid = int(mail_uid)
        plain_body_part = None
        styled_body_part = None
        imap_session.use_uid = True
        imap_session.select_folder(mailbox)
        body_structure = imap_session.fetch(mail_uid, ["BODYSTRUCTURE"])[mail_uid][b'BODYSTRUCTURE']
        body_parts = MailBodyParts(body_structure)

        query = ["BODY[HEADER]", "FLAGS"]

        if body_parts.has_styled_part():
            styled_body_part = body_parts.get_styled_part()
            query.append(styled_body_part.get_fetch_query())

        if body_parts.get_plain_part():
            plain_body_part = body_parts.get_plain_part()
            query.append(plain_body_part.get_fetch_query())

        if body_parts.has_embedded_parts():
            for part in body_parts.get_embedded_parts():
                query.append(part.get_fetch_query())

        data = imap_session.fetch(mail_uid, query)[mail_uid]

        styled_body = ""
        tnef_attachments = []

        if styled_body_part:
            if styled_body_part.is_tnef_encoded():
                styled_body, tnef_attachments = cls._decode_tnef_body(data, styled_body_part)
            else:
                styled_body = cls._decode_body(data, styled_body_part)

        # apply embedded styled_body for normal multi part mail
        if styled_body and body_parts.has_embedded_parts():
            styled_body = cls._apply_embedded_on_styled_body(data, body_parts.get_embedded_parts(), styled_body)

        # apply styled_body for tnef mail
        if styled_body and styled_body_part.is_tnef_encoded():
            styled_body = cls._apply_embedded_on_tnef_styled_body(tnef_attachments, styled_body)

        attachments = [attachment.get_attachment_data_as_dict() for attachment in body_parts.get_attachment_parts()]

        # TODO it should be with class
        for attachment in tnef_attachments:
            attachments.append({
                "part_number": attachment["part_number"],
                "content_type": attachment["content_type"],
                "content_name": attachment["content_name"],
                "content_size": attachment["content_size"],
            })

        return {
            "uid": mail_uid,
            "body": cls._decode_body(data, plain_body_part) if plain_body_part else "",
            "styled_body": styled_body,
            "flags": data.get(b'FLAGS'),
            "headers": MailParser.parse_header(data[bytes(query[0], 'utf-8')].decode()),
            "attachment": attachments
        }

    @classmethod
    @raise_command_exception
    def _apply_embedded_on_styled_body(cls, data, parts: List[MailBodyPart], styled_body: str) -> str:
        for part in parts:
            image_tag_regex = 'cid:%s' % part.part_id
            image_tag = 'data:%s;%s, %s' % (
                part.type, part.transfer_encoding.lower(), data[part.get_fetch_query_as_bytes()].decode())
            styled_body = re.sub(image_tag_regex, image_tag, styled_body)
        return styled_body

    @classmethod
    @raise_command_exception
    def _apply_embedded_on_tnef_styled_body(cls, tnef_attachments: list, styled_body: str) -> str:
        for tnef_attachment in tnef_attachments:
            if tnef_attachment["content_id"]:
                image_tag_regex = 'cid:%s' % tnef_attachment["content_id"]
                image_tag = 'data:%s;%s, %s' % (
                    tnef_attachment["content_type"], 'base64', base64.b64encode(tnef_attachment["content"]).decode())
                styled_body = re.sub(image_tag_regex, image_tag, styled_body)
        return styled_body

    @classmethod
    @raise_command_exception
    def _decode_body(cls, data, part: MailBodyPart) -> str:
        body = data[part.get_fetch_query_as_bytes()]
        return part.decode_message(body)

    @classmethod
    @raise_command_exception
    def _decode_tnef_body(cls, data, part: MailBodyPart) -> tuple:
        body = data[part.get_fetch_query_as_bytes()]
        return part.decode_tnef_message(body)

    @classmethod
    @raise_command_exception
    def fetch_by_query(cls, imap_session: IMAPClient, mail_uid: int, query: List[str]):
        imap_session.use_uid = True
        return imap_session.fetch(mail_uid, query)

    @classmethod
    @raise_command_exception
    @specified_uid_or_all
    def delete_mail(cls, imap_session: IMAPClient, mailbox: str, mail_uid: List[int]):
        imap_session.use_uid = True
        imap_session.select_folder(mailbox)
        imap_session.delete_messages(mail_uid, True)
        imap_session.expunge()

    @classmethod
    @raise_command_exception
    def download_attachment(cls, imap_session: IMAPClient, mailbox: str, mail_uid: int, part_number: str):
        mail_uid = int(mail_uid)
        imap_session.use_uid = True
        imap_session.select_folder(mailbox)
        body_parts = MailBodyParts(imap_session.fetch(mail_uid, "BODYSTRUCTURE")[mail_uid][b'BODYSTRUCTURE'])
        if body_parts.has_tnef_part():
            tnef_part = body_parts.get_tnef_part()
            if part_number.startswith(tnef_part.part_number):
                return cls._download_attachment_from_tnef_part(imap_session, mail_uid, tnef_part, part_number)
        return cls._download_attachment_from_part(imap_session, mail_uid, body_parts, part_number)

    @classmethod
    @raise_command_exception
    def _download_attachment_from_tnef_part(cls, imap_session: IMAPClient, mail_uid: int, tnef_body_part: MailBodyPart, attachment_part: str):
        query = ["BODY.PEEK[%s]" % tnef_body_part.part_number]
        data = imap_session.fetch(mail_uid, query)[mail_uid]
        tnef_body, tnef_attachmets = cls._decode_tnef_body(data, tnef_body_part)
        for attachment in tnef_attachmets:
            if attachment["part_number"] == attachment_part:
                return (
                    attachment["content"],
                    {
                        "Content-Type": attachment["content_type"],
                        "Content-Disposition": "attachment; filename=%s" % url_parser.quote(attachment["content_name"])
                    }

                )

    @classmethod
    @raise_command_exception
    def _download_attachment_from_part(cls, imap_session: IMAPClient, mail_uid: int, body_parts: MailBodyParts, attachment_part: str,):
        query = ["BODY.PEEK[%s]" % attachment_part, "BODY.PEEK[%s.MIME]" % attachment_part]
        data = imap_session.fetch(mail_uid, query)[mail_uid]
        attachment = body_parts.get_attachment_part(attachment_part)
        return (
            attachment.get_byte_decoder()(data[bytes('BODY[%s]' % attachment_part, 'utf-8')]),
            attachment.get_attachment_mime_headers()
        )

    @classmethod
    @raise_command_exception
    @specified_uid_or_all
    def copy_email(cls, imap_session: IMAPClient, mailbox: str, target_mailbox: str, mail_uid: List[int]):
        imap_session.select_folder(mailbox)
        imap_session.use_uid = True
        imap_session.copy(mail_uid, target_mailbox)

    @classmethod
    @raise_command_exception
    def append_mail(cls, imap_session: IMAPClient, mailbox: str, body: str, headers: List[dict],
                    attachments: List[dict], styled_body: str = None):
        message = utils.construct_mail_message(body, styled_body, headers, attachments)
        from_address = "%s <%s>" % (imap_session.user.get("name", ""), imap_session.user.get("email"))
        message.add_header("From", from_address)
        imap_session.append(mailbox, message.as_bytes(), ("\\Seen",))

    @classmethod
    @raise_command_exception
    @specified_uid_or_all
    def add_flags(cls, imap_session: IMAPClient, mailbox: str, mail_uid: List[int], flags: List[str]):
        imap_session.use_uid = True
        imap_session.select_folder(mailbox)
        imap_session.add_flags(mail_uid, flags)

    @classmethod
    @raise_command_exception
    @specified_uid_or_all
    def remove_flags(cls, imap_session: IMAPClient, mailbox: str, mail_uid: List[int], flags: List[str]):
        imap_session.use_uid = True
        imap_session.select_folder(mailbox)
        imap_session.remove_flags(mail_uid, flags)

    @classmethod
    def _get_brief(cls, part: MailBodyPart, uid: int, imap_session: IMAPClient):
        data = cls.fetch_by_query(imap_session, uid, ["BODY.PEEK[%s]" % part.part_number])
        peek = "BODY[%s]" % part.part_number
        return part.decode_message(data.get(uid).get(bytes(peek, 'utf-8')))[:200]

    @classmethod
    def _construct_envelope(cls, data: dict) -> dict:
        envelope = data.get(b'ENVELOPE')
        flags = data.get(b'FLAGS')
        uid = data.get(b'UID')
        body_parts = MailBodyParts(data.get(b'BODYSTRUCTURE'))
        priority_headers = MailParser.parse_priority_header(
            data.get(b'BODY[HEADER.FIELDS (X-PRIORITY IMPORTANCE)]').decode())
        date = int(envelope.date.timestamp()) if envelope.date else None
        brief = ""
        # TODO refactor for brief
        try:
            brief = data.get(b'BODY[1]<0>').decode()[0:min(body_parts.get_plain_part().size, 35)] if body_parts.has_plain_part() else ""
        except Exception as e:
            pass
        subject = MailParser.decode_header_value(envelope.subject.decode()) if envelope.subject else ""
        sender = cls._construct_envelope_user_address(envelope.sender[0]) if envelope.sender else ""
        to_list = [cls._construct_envelope_user_address(to) for to in envelope.to or []]
        cc_list = [cls._construct_envelope_user_address(cc) for cc in envelope.cc or []]
        bcc_list = [cls._construct_envelope_user_address(bcc) for bcc in envelope.bcc or []]

        return {
            "flags": flags,
            "subject": subject,
            "date": date,
            "sender": sender,
            "to": to_list,
            "cc": cc_list,
            "bcc": bcc_list,
            "brief": brief,
            "uid": uid,
            "priority_name": priority_headers["priority_name"],
            "priority_value": priority_headers["priority_value"],
            "attachment": [attachment.get_attachment_data_as_dict() for attachment in body_parts.get_attachment_parts()]
        }

    @classmethod
    def _get_paged_response(cls, pager: MailPager, result: List) -> dict:
        return {
            "total_items": pager.total,
            "total_pages": pager.pages,
            "current_page": pager.page,
            "items": result
        }

    @classmethod
    def _adders_part_exists(cls, address_part: bytes) -> bool:
        return address_part and address_part.decode() not in cls.MISSING_ADDRESS_VALUES

    @classmethod
    def _construct_envelope_user_address(cls, address: Address) -> str:
        mail_user = address.mailbox.decode() if cls._adders_part_exists(address.mailbox) else ""
        mail_domain = "@%s" % address.host.decode() if cls._adders_part_exists(address.host) else ""
        mail_address = "%s%s" % (mail_user, mail_domain)
        if address.name is not None and address.name != "":
            return "%s <%s>" % (address.name.decode(), mail_address)
        else:
            return mail_address

    @classmethod
    def _get_default_search(cls, search_criteria: list, imap_session) -> list:
        search_criteria = search_criteria if search_criteria else []
        if "SENTSINCE" in search_criteria:
            date_index = search_criteria.index("SENTSINCE")
            search_criteria.pop(date_index)
            search_criteria.pop(date_index)
        return search_criteria
