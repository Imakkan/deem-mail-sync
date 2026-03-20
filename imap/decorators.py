from .exceptions import IMAPCommandException


def raise_command_exception(fun):
    def decorator(*args, **kwargs):
        try:
            result = fun(*args, **kwargs)
        except Exception as e:
            raise IMAPCommandException(e)
        return result
    return decorator


def specified_uid_or_all(fun):
    def decorator(*args, **kwargs):
        mail_uid = kwargs.get("mail_uid")
        if not mail_uid and mail_uid is not None:
            kwargs["mail_uid"] = "1:*"
        result = fun(*args, **kwargs)
        return result
    return decorator
