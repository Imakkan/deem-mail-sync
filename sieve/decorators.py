from sieve.exceptions import SieveCommandException


def raise_command_exception(fun):
    def decorator(*args, **kwargs):
        try:
            result = fun(*args, **kwargs)
        except Exception as e:
            raise SieveCommandException(e)
        return result
    return decorator
