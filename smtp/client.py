from smtplib import SMTP
from .exceptions import SMTPConnectionException, SMTPAuthenticationException


class Client:

    def __init__(self, host, port):
        try:
            self.session = SMTP(host=host, port=port)
        except Exception as e:
            raise SMTPConnectionException(e)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()

    def login(self, username, token):
        self.session.user = username
        try:
            self.session.auth("XOAUTH2", lambda x: token, initial_response_ok=False)
        except Exception as e:
            raise SMTPAuthenticationException(e)

    def logout(self, ):
        self.session.quit()
