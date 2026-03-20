from imapclient import IMAPClient
from .exceptions import IMAPConnectionException, IMAPAuthenticationException


class Client:

    def __init__(self, host, port, master_username="", master_password=""):
        self.master_username = master_username
        self.master_password = master_password
        try:
            self.session = IMAPClient(host=host, port=port, ssl=False, use_uid=False)
        except Exception as e:
            raise IMAPConnectionException(e)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()

    def login(self, username, token):
        self.session.user = username
        try:
            self.session.oauth2_login(self.session.user.get("email"), token)
        except Exception as e:
            raise IMAPAuthenticationException(e)

    def login_master(self, username):
        self.session.user = username
        try:
            self.session.login("%s*%s" % (self.session.user.get("email"), self.master_username), self.master_password)
        except Exception as e:
            raise IMAPConnectionException(e)

    def logout(self,):
        self.session.logout()
