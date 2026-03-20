from .exceptions import SMTPCommandException


def raise_command_exception(fun):
    def decorator(*args, **kwargs):
        try:
            result = fun(*args, **kwargs)
        except Exception as e:
            raise SMTPCommandException(e)
        return result
    return decorator
