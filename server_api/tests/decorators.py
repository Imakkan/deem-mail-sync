from unittest.mock import patch


def imap_session_decorator(fun):
    @patch("imapclient.IMAPClient.__init__", return_value=None)
    @patch("imapclient.IMAPClient.oauth2_login")
    @patch("imapclient.IMAPClient.login")
    @patch("imapclient.IMAPClient.logout")
    def decorator(obj, logout_mock, login_mock, login_oauth2_mock, init_mock, *args, **kwargs):
        return fun(obj, *args, **kwargs)

    return decorator


def smtp_session_decorator(fun):
    @patch("smtplib.SMTP.__init__", return_value=None)
    @patch("smtplib.SMTP.auth")
    @patch("smtplib.SMTP.quit")
    def decorator(obj, quit_mock, login_mock, init_mock, *args, **kwargs):
        return fun(obj, *args, **kwargs)

    return decorator
