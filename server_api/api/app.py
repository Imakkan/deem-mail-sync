import http
import logging

from fastapi import Request, HTTPException, Response, Header
from pydantic.error_wrappers import ValidationError

from imap.client import Client as IMAPSession
from imap.command import Command as IMAPCommand
from smtp.client import Client as SMTPSession
from sieve.client import Client as SieveSession
from server_api.api.enumerate import Context
from server_api.models.common import MailCommand
from server_api.settings.config import app, env
from server_api.api.decorators import raise_mail_exception
from .commands import command_map

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@raise_mail_exception
def perform_imap_command(request, function, **kwargs):
    imap_settings = env["IMAP_SETTINGS"]

    with IMAPSession(imap_settings.get("host"), imap_settings.get("port")) as imap:
        imap.login(request.state.mail_user, request.state.mail_sasl_token)
        result = function(imap.session, **kwargs)
    if isinstance(result, tuple):
        return Response(content=result[0], headers=result[1])
    return result


@raise_mail_exception
def perform_master_imap_command(request, function, **kwargs):
    imap_settings = env["IMAP_MASTER_SETTINGS"]
    master_settings = env["MASTER_SETTINGS"]

    with IMAPSession(imap_settings.get("host"), imap_settings.get("port"),
                     master_settings.get("username"), master_settings.get("password")) as imap:
        imap.login_master(request.state.mail_user)
        result = function(imap.session, **kwargs)
    if isinstance(result, tuple):
        return Response(content=result[0], headers=result[1])
    return result


@raise_mail_exception
def perform_smtp_command(request, function, **kwargs):
    smtp_settings = env["SMTP_SETTINGS"]
    with SMTPSession(smtp_settings.get("host"), smtp_settings.get("port")) as smtp:
        smtp.login(request.state.mail_user, request.state.mail_sasl_token)
        result = function(smtp.session, **kwargs)
    return result


@raise_mail_exception
def perform_master_smtp_command(request, function, **kwargs):
    raise HTTPException(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail="perform command as master for SMTP protocol is not supported")


@raise_mail_exception
def perform_sieve_command(request, function, **kwargs):
    sieve_settings = env["SIEVE_SETTINGS"]

    with SieveSession(sieve_settings["host"], sieve_settings["port"]) as sieve:
        sieve.login(request.state.mail_user, request.state.mail_sasl_token)
        result = function(sieve.session, **kwargs)
    return result


def perform_command(request: Request, body: MailCommand, command_call):
    mail_command = command_map[body.command.value]
    if mail_command.has_arguments():
        try:
            mail_command_model = mail_command.model(**body.arguments) if mail_command.has_arguments() else None
        except ValidationError as e:
            raise HTTPException(status_code=http.HTTPStatus.UNPROCESSABLE_ENTITY, detail=e.errors())
        return command_call(request, mail_command.function, **mail_command_model.dict())
    return command_call(request, mail_command.function)


context_map = {
    "IMAP": perform_imap_command,
    "SMTP": perform_smtp_command,
    "Sieve": perform_sieve_command
}


@app.post("/command")
def command(request: Request, body: MailCommand):
    logger.info(" user: %s, command: %s" % (request.state.mail_user["email"], body.command.value))
    mail_command = command_map[body.command.value]
    command_call = context_map[mail_command.context]
    return perform_command(request, body, command_call)


@app.post("/master/command")
def master_command(request: Request, body: MailCommand):
    mail_command = command_map[body.command.value]
    command_call = perform_master_imap_command if mail_command.context is Context.IMAP else perform_master_smtp_command
    return perform_command(request, body, command_call)


@app.get("/api/email/download-attachment")
def download_attachment(request: Request, mailbox: str, uid: int, part: str):
    result = perform_imap_command(
        request, IMAPCommand.download_attachment, mailbox=mailbox, mail_uid=uid, part_number=part
    )
    return result
