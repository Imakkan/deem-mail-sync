import base64

from fastapi.testclient import TestClient as FastApiClient
from server_api.models.common import Command
from requests import Response


class CommandTestClient(FastApiClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def _construct_authorization_header(cls) -> str:
        authorization_header = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9'
        authorization_body = 'eyJlbWFpbCI6InVzZXIxQGhvbWUub3JnIiwibmFtZSI6InVzZXIgbmFtZSJ9'
        authorization_signature = 'rCdqWNoH7h9-mIzXhOgFn1FJZvD1cTbD9YhckaXgK7Q'
        return "Bearer %s.%s.%s" % (authorization_header, authorization_body, authorization_signature)

    @classmethod
    def _construct_master_authorization_header(cls) -> str:
        return "Bearer %s" % base64.standard_b64encode(bytes("user1@home.org", "utf-8")).decode()

    def perform_command(self, command: Command, arguments: dict, *args, **kwargs) -> Response:
        headers = dict()
        body = dict()
        headers["Authorization"] = self._construct_authorization_header()
        body["command"] = command.value
        body["arguments"] = arguments
        return super().post("/command", *args, headers=headers, json=body, **kwargs)

    def perform_master_command(self, command: Command, arguments: dict, *args, **kwargs) -> Response:
        headers = dict()
        body = dict()
        headers["Authorization"] = self._construct_master_authorization_header()
        body["command"] = command.value
        body["arguments"] = arguments
        return super().post("/master/command", *args, headers=headers, json=body, **kwargs)

    def download_attachment(self, mailbox: str, uid: int, part: int):
        headers = dict()
        headers["Authorization"] = self._construct_authorization_header()
        params = "mailbox=%s&uid=%s&part=%s" % (mailbox, uid, part)
        return super().get("/api/email/download-attachment", params=params, headers=headers)


class BasicTestClass:

    @classmethod
    def is_equal(cls, first_arg, second_arg):
        assert first_arg == second_arg
