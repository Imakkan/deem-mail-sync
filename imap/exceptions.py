class IMAPConnectionException(Exception):
    pass


class IMAPCommandException(Exception):
    pass


class IMAPAuthenticationException(Exception):
    pass


class DeleteDefaultMailboxException(Exception):
    pass


class RenameDefaultMailboxException(Exception):
    pass
