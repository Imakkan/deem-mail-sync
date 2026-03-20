from server_api.api.enumerate import Command, Context
from server_api.models.smtp import SendMail
from server_api.models.imap import (ListMail, FetchMail, AppendMail, CopyMail, DeleteMail, Flags, CreateMailbox,
                                    RenameMailbox, DeleteMailbox, PeekMail, DownloadAttachment)
from server_api.models.sieve import PutAutoreplyScript, PutScript
from server_api.api.utils import EmailCommand
from imap.command import Command as IMAPCommand
from smtp.command import Command as SMTPCommand
from sieve.command import Command as SieveCommand

command_map = {
    # Imap commands
    Command.LIST_MAIL.value: EmailCommand(IMAPCommand.list_mails, Context.IMAP, ListMail),
    Command.LIST_MAILBOX.value: EmailCommand(IMAPCommand.list_mail_boxes, Context.IMAP, None),
    Command.FETCH_MAIL.value: EmailCommand(IMAPCommand.fetch_mail, Context.IMAP, FetchMail),
    Command.PEEK_MAIL.value: EmailCommand(IMAPCommand.peek_mail, Context.IMAP, PeekMail),
    Command.DOWNLOAD_ATTACHMENT.value: EmailCommand(IMAPCommand.download_attachment, Context.IMAP, DownloadAttachment),
    Command.APPEND_MAIL.value: EmailCommand(IMAPCommand.append_mail, Context.IMAP, AppendMail),
    Command.COPY_MAIL.value: EmailCommand(IMAPCommand.copy_email, Context.IMAP, CopyMail),
    Command.DELETE_MAIL.value: EmailCommand(IMAPCommand.delete_mail, Context.IMAP, DeleteMail),
    Command.ADD_FLAGS.value: EmailCommand(IMAPCommand.add_flags, Context.IMAP, Flags),
    Command.REMOVE_FLAGS.value: EmailCommand(IMAPCommand.remove_flags, Context.IMAP, Flags),
    Command.CREATE_MAILBOX.value: EmailCommand(IMAPCommand.create_mail_box, Context.IMAP, CreateMailbox),
    Command.RENAME_MAILBOX.value: EmailCommand(IMAPCommand.rename_mail_box, Context.IMAP, RenameMailbox),
    Command.DELETE_MAILBOX.value: EmailCommand(IMAPCommand.delete_mail_box, Context.IMAP, DeleteMailbox),

    # Smtp commands
    Command.SEND_MAIL.value: EmailCommand(SMTPCommand.send_email, Context.SMTP, SendMail),

    # Sieve commands
    Command.GET_AUTOREPLY_SCRIPT.value: EmailCommand(SieveCommand.get_autoreply_script, Context.Sieve, None),
    Command.PUT_AUTOREPLY_SCRIPT.value: EmailCommand(SieveCommand.put_autoreply_script, Context.Sieve,
                                                     PutAutoreplyScript),
    Command.ACTIVATE_AUTOREPLY_SCRIPT.value: EmailCommand(SieveCommand.activate_autoreply_script, Context.Sieve, None),
    Command.DEACTIVATE_AUTOREPLY_SCRIPT.value: EmailCommand(SieveCommand.deactivate_autoreply_script, Context.Sieve,
                                                            None),
    Command.PUT_SCRIPT.value: EmailCommand(SieveCommand.put_script, Context.Sieve, PutScript)
}
