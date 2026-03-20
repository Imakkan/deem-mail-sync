import base64

from managesieve import MANAGESIEVE
from sieve.exceptions import SieveConnectionException, SieveAuthenticationException


class Client:
    def __init__(self, host, port):
        try:
            self.session = MANAGESIEVE(host=host, port=port, use_tls=False)
        except Exception as e:
            raise SieveConnectionException

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()

    def login(self, username, token):
        self.session.user = username
        try:
            b64_token = base64.b64encode(token.encode()).decode("utf-8")
            b64_token_quoted = ('"%s"' % b64_token).encode()
            self.session._command(b'AUTHENTICATE',  b'"XOAUTH2"', b64_token_quoted)
            self.session.state = "AUTH"
        except Exception as e:
            raise SieveAuthenticationException

    def logout(self):
        self.session.logout()
