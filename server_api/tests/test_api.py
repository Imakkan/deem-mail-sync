from http import HTTPStatus

import pytest

from server_api.models.common import Command
from server_api.api.app import app
from .utils import CommandTestClient, BasicTestClass
from unittest.mock import patch, MagicMock
from .decorators import imap_session_decorator, smtp_session_decorator
from .data import MockedData, Arguments

client = CommandTestClient(app)


class TestImapErrorHandling(BasicTestClass):

    @imap_session_decorator
    @patch("imapclient.IMAPClient.folder_status")
    @patch("imapclient.IMAPClient.sort")
    @patch("imapclient.IMAPClient.list_folders")
    def test_imap_command_exception(self, list_folders_mock: MagicMock, sort_mock: MagicMock,
                                    folder_status_mock: MagicMock):
        sort_mock.return_value = [1, 2]
        list_folders_mock.side_effect = Exception("an exception inside command")
        response = client.perform_command(Command.LIST_MAILBOX, dict())
        self.is_equal(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        list_folders_mock.assert_called_once()
        folder_status_mock.assert_not_called()

    def test_entity_command_exception(self):
        response = client.perform_command(Command.FETCH_MAIL, dict())
        self.is_equal(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY)

    @patch("imapclient.IMAPClient.__init__", return_value=None)
    @patch("imapclient.IMAPClient.logout")
    @patch("imapclient.IMAPClient.oauth2_login")
    def test_imap_authentication_exception(self, login_mock: MagicMock, *args):
        login_mock.side_effect = Exception("an exception inside login")
        response = client.perform_command(Command.LIST_MAILBOX, dict())
        self.is_equal(response.status_code, HTTPStatus.UNAUTHORIZED)
        login_mock.assert_called_once()

    @patch("imapclient.IMAPClient.__init__")
    def test_imap_connection_exception(self, init_mock: MagicMock):
        init_mock.side_effect = Exception("an exception inside connection")
        response = client.perform_command(Command.LIST_MAILBOX, dict())
        self.is_equal(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)
        init_mock.assert_called_once()

    @patch("imapclient.IMAPClient.__init__")
    def test_imap_other_exception(self, *args):
        response = client.perform_command(Command.LIST_MAILBOX, dict())
        self.is_equal(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)


class TestImap(BasicTestClass):

    @imap_session_decorator
    @patch("imapclient.IMAPClient.folder_status")
    @patch("imapclient.IMAPClient.list_folders")
    def test_master_command(self, list_folders_mock: MagicMock, folder_status_mock: MagicMock):
        list_folders_mock.return_value = MockedData.get_mailboxes()
        folder_status_mock.return_value = MockedData.get_mailbox_status()

        response = client.perform_master_command(Command.LIST_MAILBOX, dict())

        self.is_equal(response.status_code, HTTPStatus.OK)
        list_folders_mock.assert_called_once()
        folder_status_mock.assert_called_once()

    @imap_session_decorator
    @patch("imapclient.IMAPClient.folder_status")
    @patch("imapclient.IMAPClient.list_folders")
    def test_list_mailbox(self, list_folders_mock: MagicMock, folder_status_mock: MagicMock):
        list_folders_mock.return_value = MockedData.get_mailboxes()
        folder_status_mock.return_value = MockedData.get_mailbox_status()

        response = client.perform_command(Command.LIST_MAILBOX, dict())

        self.is_equal(response.status_code, HTTPStatus.OK)
        list_folders_mock.assert_called_once()
        folder_status_mock.assert_called_once()

    @imap_session_decorator
    @patch("imapclient.IMAPClient.create_folder")
    @patch("imapclient.IMAPClient.subscribe_folder")
    def test_create_mailbox(self, create_folder_mock: MagicMock, subscribe_folder_mock: MagicMock):
        response = client.perform_command(Command.CREATE_MAILBOX, Arguments.get_create_mailbox_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        create_folder_mock.assert_called_once()
        subscribe_folder_mock.assert_called_once()

    @imap_session_decorator
    @patch("imapclient.IMAPClient.unsubscribe_folder")
    @patch("imapclient.IMAPClient.delete_folder")
    def test_delete_mailbox(self, unsubscribe_folder_mock: MagicMock, delete_folder_mock: MagicMock):
        response = client.perform_command(Command.DELETE_MAILBOX, Arguments.get_delete_mailbox_arguments())
        self.is_equal(response.status_code, HTTPStatus.OK)
        unsubscribe_folder_mock.assert_called_once()
        delete_folder_mock.assert_called_once()

    @imap_session_decorator
    @patch("imapclient.IMAPClient.unsubscribe_folder")
    @patch("imapclient.IMAPClient.delete_folder")
    def test_delete_default_mailbox(self, unsubscribe_folder_mock: MagicMock, delete_folder_mock: MagicMock):
        response = client.perform_command(Command.DELETE_MAILBOX, Arguments.get_delete_default_mailbox_arguments())
        self.is_equal(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        unsubscribe_folder_mock.assert_not_called()
        delete_folder_mock.assert_not_called()

    @imap_session_decorator
    @patch("imapclient.IMAPClient.rename_folder")
    def test_rename_mailbox(self, rename_folder_mock: MagicMock):
        response = client.perform_command(Command.RENAME_MAILBOX, Arguments.get_rename_mailbox_arguments())
        self.is_equal(response.status_code, HTTPStatus.OK)
        rename_folder_mock.assert_called_once()

    @imap_session_decorator
    @patch("imapclient.IMAPClient.rename_folder")
    def test_rename_default_mailbox(self, rename_folder_mock: MagicMock):
        response = client.perform_command(Command.RENAME_MAILBOX, Arguments.get_rename_default_mailbox_arguments())
        self.is_equal(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        rename_folder_mock.assert_not_called()

    @imap_session_decorator
    @patch("imapclient.IMAPClient.select_folder")
    def test_list_mails_return_empty(self, select_folder_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(0)

        response = client.perform_command(Command.LIST_MAIL, Arguments.get_list_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once()

    @imap_session_decorator
    @patch("imapclient.IMAPClient.fetch")
    @patch("imapclient.IMAPClient.sort")
    @patch("imapclient.IMAPClient.select_folder")
    def test_list_mails_success(self, select_folder_mock: MagicMock, sort_mock: MagicMock, fetch_mock: MagicMock):
        sort_mock.return_value = [1, 2]
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        fetch_mock.return_value = MockedData.get_fetch_return_value()

        response = client.perform_command(Command.LIST_MAIL, Arguments.get_list_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once()
        fetch_mock.assert_called()
        sort_mock.assert_called_once()

    @imap_session_decorator
    @patch("imapclient.IMAPClient.sort")
    @patch("imapclient.IMAPClient.fetch")
    @patch("imapclient.IMAPClient.select_folder")
    def test_list_mails_with_search_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock,
                                            sort_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        fetch_mock.return_value = MockedData.get_fetch_with_priority_return_value()
        sort_mock.return_value = [1, 2]

        response = client.perform_command(Command.LIST_MAIL, Arguments.get_list_mail_arguments(["TEXT", "some"]))

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once()
        fetch_mock.assert_called()
        sort_mock.assert_called_once()

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_fetch_mail_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        fetch_mock.return_value = MockedData.get_fetch_return_value()

        response = client.perform_command(Command.FETCH_MAIL, Arguments.get_fetch_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once_with('INBOX')
        self.is_equal(fetch_mock.call_count, 2)

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_peek_mail_success(self, select_folder_mock: MagicMock, peek_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        peek_mock.return_value = MockedData.get_peek_return_value()

        response = client.perform_command(Command.PEEK_MAIL, Arguments.get_fetch_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once_with('INBOX')
        self.is_equal(peek_mock.call_count, 1)

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_fetch_mail_recursive_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        fetch_mock.return_value = MockedData.get_fetch_recursive_return_value()

        response = client.perform_command(Command.FETCH_MAIL, Arguments.get_fetch_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once_with('INBOX')
        self.is_equal(fetch_mock.call_count, 2)

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_fetch_mail_with_arabic_subject_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        fetch_mock.return_value = MockedData.get_fetch_with_arabic_subject_return_value()

        response = client.perform_command(Command.FETCH_MAIL, Arguments.get_fetch_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once_with('INBOX')
        self.is_equal(fetch_mock.call_count, 2)

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_fetch_with_styled_mail_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        fetch_mock.return_value = MockedData.get_fetch_with_styled_body_return_value()

        response = client.perform_command(Command.FETCH_MAIL, Arguments.get_fetch_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once_with('INBOX')
        self.is_equal(fetch_mock.call_count, 2)

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_fetch_with_only_styled_mail_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        fetch_mock.return_value = MockedData.get_fetch_with_only_styled_body_return_value()

        response = client.perform_command(Command.FETCH_MAIL, Arguments.get_fetch_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once_with('INBOX')
        self.is_equal(fetch_mock.call_count, 2)

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_fetch_with_quoted_styled_mail_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        fetch_mock.return_value = MockedData.get_fetch_with_quoted_styled_body_return_value()

        response = client.perform_command(Command.FETCH_MAIL, Arguments.get_fetch_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once_with('INBOX')
        self.is_equal(fetch_mock.call_count, 2)

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_fetch_with_attachment_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        fetch_mock.return_value = MockedData.get_fetch_with_attachment_return_value()

        response = client.perform_command(Command.FETCH_MAIL, Arguments.get_fetch_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once_with('INBOX')
        self.is_equal(fetch_mock.call_count, 2)

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_fetch_with_embedded_images_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        fetch_mock.return_value = MockedData.get_fetch_with_embedded_image_return_value()

        response = client.perform_command(Command.FETCH_MAIL, Arguments.get_fetch_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once_with('INBOX')
        self.is_equal(fetch_mock.call_count, 2)

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_fetch_with_attachment_without_name_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock):
        select_folder_mock.return_value = MockedData.get_select_folder_return_value(1)
        fetch_mock.return_value = MockedData.get_fetch_with_attachment_without_name_return_value()

        response = client.perform_command(Command.FETCH_MAIL, Arguments.get_fetch_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once_with('INBOX')
        self.is_equal(fetch_mock.call_count, 2)

    @imap_session_decorator
    @patch('imapclient.IMAPClient.append')
    def test_append_mail_success(self, append_mock: MagicMock):
        response = client.perform_command(Command.APPEND_MAIL, Arguments.get_append_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        append_mock.assert_called_once()

    @imap_session_decorator
    @patch('imapclient.IMAPClient.copy')
    @patch('imapclient.IMAPClient.select_folder')
    def test_copy_mail_success(self, select_mock: MagicMock, copy_mock: MagicMock):
        response = client.perform_command(Command.COPY_MAIL, Arguments.get_copy_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        copy_mock.assert_called_once()
        select_mock.assert_called_once()

    @imap_session_decorator
    @patch('imapclient.IMAPClient.expunge')
    @patch('imapclient.IMAPClient.delete_messages')
    @patch('imapclient.IMAPClient.select_folder')
    def test_delete_mail_success(self, select_mock: MagicMock, delete_mock: MagicMock, expunge_mock: MagicMock):
        response = client.perform_command(Command.DELETE_MAIL, Arguments.get_delete_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_mock.assert_called_once()
        delete_mock.assert_called_once()
        expunge_mock.assert_called_once()

    @imap_session_decorator
    @patch('imapclient.IMAPClient.expunge')
    @patch('imapclient.IMAPClient.delete_messages')
    @patch('imapclient.IMAPClient.select_folder')
    def test_delete_all_mail_success(self, select_mock: MagicMock, delete_mock: MagicMock, expunge_mock: MagicMock):
        response = client.perform_command(Command.DELETE_MAIL, Arguments.get_delete_all_mail_arguments())

        self.is_equal(response.status_code, HTTPStatus.OK)
        select_mock.assert_called_once()
        delete_mock.assert_called_once()
        expunge_mock.assert_called_once()

    @imap_session_decorator
    @patch('imapclient.IMAPClient.add_flags')
    @patch('imapclient.IMAPClient.select_folder')
    def test_add_flags_success(self, select_folder_mock: MagicMock, add_flags_mock: MagicMock):
        response = client.perform_command(Command.ADD_FLAGS, Arguments.get_flags_arguments())
        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once()
        add_flags_mock.assert_called_once()

    @imap_session_decorator
    @patch('imapclient.IMAPClient.remove_flags')
    @patch('imapclient.IMAPClient.select_folder')
    def test_remove_flags_success(self, select_folder_mock: MagicMock, remove_flags_mock: MagicMock):
        response = client.perform_command(Command.REMOVE_FLAGS, Arguments.get_flags_arguments())
        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once()
        remove_flags_mock.assert_called_once()

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_download_attachment_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock, *args, **kwargs):
        mailbox = "INBOX"
        uid = 1
        part = 1
        fetch_mock.return_value = MockedData.get_fetch_attachment()

        response = client.download_attachment(mailbox=mailbox, uid=uid, part=part)
        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once()
        fetch_mock.assert_called_once()

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_download_attachment_disposition_filename_messing_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock, *args, **kwargs):
        mailbox = "INBOX"
        uid = 1
        part = 1
        fetch_mock.return_value = MockedData.get_fetch_attachment_with_disposition_filename_messing()

        response = client.download_attachment(mailbox=mailbox, uid=uid, part=part)
        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once()
        fetch_mock.assert_called_once()

    @imap_session_decorator
    @patch('imapclient.IMAPClient.fetch')
    @patch('imapclient.IMAPClient.select_folder')
    def test_download_attachment_filename_messing_success(self, select_folder_mock: MagicMock, fetch_mock: MagicMock, *args, **kwargs):
        mailbox = "INBOX"
        uid = 1
        part = 1
        fetch_mock.return_value = MockedData.get_fetch_attachment_with_filename_messing()

        response = client.download_attachment(mailbox=mailbox, uid=uid, part=part)
        self.is_equal(response.status_code, HTTPStatus.OK)
        select_folder_mock.assert_called_once()
        fetch_mock.assert_called_once()


class TestSmtpErrorHandling(BasicTestClass):

    @patch("smtplib.SMTP.__init__")
    def test_smtp_client_fail(self, smtp_init_mock: MagicMock):
        smtp_init_mock.side_effect = Exception("some smpt client exception")

        response = client.perform_command(Command.SEND_MAIL, Arguments.get_send_email_arguments())
        self.is_equal(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    @patch("smtplib.SMTP.__init__", return_value=None)
    @patch("smtplib.SMTP.auth")
    def test_smtp_auth_fail(self, smtp_auth_mock: MagicMock, smtp_init_mock: MagicMock):
        smtp_auth_mock.side_effect = Exception("some smpt auth exception")
        response = client.perform_command(Command.SEND_MAIL, Arguments.get_send_email_arguments())
        self.is_equal(response.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    @smtp_session_decorator
    @patch("smtplib.SMTP.send_message")
    def test_send_success(self, send_message_mock: MagicMock):
        send_message_mock.side_effect = Exception("some command exception")

        response = client.perform_command(Command.SEND_MAIL, Arguments.get_send_email_arguments())
        self.is_equal(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        send_message_mock.assert_called_once()


class TestSmtp(BasicTestClass):

    @smtp_session_decorator
    @patch("smtplib.SMTP.send_message")
    def test_send_success(self, send_message_mock: MagicMock):
        send_message_mock.return_value = {}

        response = client.perform_command(Command.SEND_MAIL, Arguments.get_send_email_arguments())
        self.is_equal(response.status_code, HTTPStatus.OK)
        send_message_mock.assert_called_once()

    @smtp_session_decorator
    @patch("smtplib.SMTP.send_message")
    def test_send_with_styled_bod_success(self, send_message_mock: MagicMock):
        send_message_mock.return_value = {}

        response = client.perform_command(Command.SEND_MAIL, Arguments.get_send_email_with_styled_body_arguments())
        self.is_equal(response.status_code, HTTPStatus.OK)
        send_message_mock.assert_called_once()

    @smtp_session_decorator
    @patch("smtplib.SMTP.send_message")
    def test_send_with_attachments_success(self, send_message_mock: MagicMock):
        send_message_mock.return_value = {}

        response = client.perform_command(Command.SEND_MAIL, Arguments.get_send_email_wit_attachment_arguments())
        self.is_equal(response.status_code, HTTPStatus.OK)
        send_message_mock.assert_called_once()

    @smtp_session_decorator
    @patch("smtplib.SMTP.send_message")
    def test_send_with_attachments_content_id_success(self, send_message_mock: MagicMock):
        send_message_mock.return_value = {}

        response = client.perform_command(Command.SEND_MAIL, Arguments.get_send_email_wit_attachment_arguments())
        self.is_equal(response.status_code, HTTPStatus.OK)
        send_message_mock.assert_called_once()
