from typing import List

from sievelib.commands import get_command_instance
from sievelib.parser import Parser, Lexer

from sieve.builder import ConditionBuilder, ActionBuilder
from sieve.decorators import raise_command_exception
from managesieve import MANAGESIEVE
from sievelib.factory import FiltersSet

from sieve.utils import construct_sieve_mime_body, deconstruct_sieve_mime_body


class Command:
    AUTOREPLY_SCRIPT_NAME = 'autoreply'

    class SieveResponseConstant:
        FAILURE = 'NO'
        SUCCESS = 'OK'
        CONNECTION_END = 'BYE'

    @classmethod
    def _get_sieve_subject(cls, parser: Parser) -> str:
        return str(parser.result[1].children[0].extra_arguments['subject']).replace('\"', '')

    @classmethod
    def _get_sieve_mime_body(cls, parser: Parser) -> str:
        return str(parser.result[1].children[0].arguments['reason'])

    @classmethod
    def _is_autoreply_acitve(cls, sieve_client: MANAGESIEVE) -> bool:
        response = sieve_client.listscripts()
        if response[0] == cls.SieveResponseConstant.SUCCESS:
            for script_name, is_active in response[1]:
                if script_name == cls.AUTOREPLY_SCRIPT_NAME and is_active:
                    return True
        return False

    @classmethod
    def _get_autoreply_script(cls, sieve_client: MANAGESIEVE):
        subject = ""
        body = ""
        style_body = ""
        script = sieve_client.getscript(cls.AUTOREPLY_SCRIPT_NAME)
        parser = Parser()
        if script[0] == cls.SieveResponseConstant.FAILURE or not parser.parse(script[1]):
            return subject, body, style_body

        subject = cls._get_sieve_subject(parser)
        (body, style_body) = deconstruct_sieve_mime_body(cls._get_sieve_mime_body(parser))
        return subject, body, style_body

    @classmethod
    @raise_command_exception
    def get_autoreply_script(cls, sieve_client: MANAGESIEVE) -> dict:

        is_active = cls._is_autoreply_acitve(sieve_client)
        subject, body, style_body = cls._get_autoreply_script(sieve_client)

        return {
            "subject": subject,
            "body": body,
            "style_body": style_body,
            "is_active": is_active
        }

    @classmethod
    @raise_command_exception
    def put_autoreply_script(cls, sieve_client: MANAGESIEVE, subject: str, body: str, styled_body: str = None):
        message = construct_sieve_mime_body(body, styled_body)
        filter_set = FiltersSet(cls.AUTOREPLY_SCRIPT_NAME)
        filter_set.require("vacation")
        filter_set.addfilter(cls.AUTOREPLY_SCRIPT_NAME, [], [('vacation', ':subject', '"%s"' % subject,
                                                              ':mime', message)], 'true')
        result = sieve_client.putscript(cls.AUTOREPLY_SCRIPT_NAME, str(filter_set))
        return result

    @classmethod
    @raise_command_exception
    def activate_autoreply_script(cls, sieve_client: MANAGESIEVE):
        result = sieve_client.setactive(cls.AUTOREPLY_SCRIPT_NAME)
        return result

    @classmethod
    @raise_command_exception
    def deactivate_autoreply_script(cls, sieve_client: MANAGESIEVE):
        result = sieve_client.setactive('')
        return result

    @classmethod
    @raise_command_exception
    def put_script(cls, sieve_client: MANAGESIEVE, rules: List):
        filter_set = FiltersSet(sieve_client.user['email'])
        requires = []
        actions = []
        conditions = []
        for rule in rules:
            conditions = []
            actions = []
            if rule.get('conditions') and rule.get('conditions').get('values') and \
                    len(rule['conditions']['values']) > 0:
                ConditionBuilder.build_conditions(sieve_client.user['email'], conditions, rule['conditions']['values'])
            if rule.get('actions') and len(rule['actions']) > 0:
                ActionBuilder.build_actions(requires, actions, rule['actions'])
            filter_set.requires = requires
            filter_set.addfilter(rule['uuid'], conditions, actions, rule['conditions']['match_type'])

        result = sieve_client.putscript(sieve_client.user['email'], str(filter_set))
        if result == cls.SieveResponseConstant.SUCCESS:
            sieve_client.setactive(sieve_client.user['email'])

        return result
