import logging
import http

from imap.exceptions import (IMAPConnectionException, IMAPAuthenticationException, IMAPCommandException)
from smtp.exceptions import (SMTPCommandException, SMTPAuthenticationException, SMTPConnectionException)
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def raise_mail_exception(func):
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (IMAPConnectionException, SMTPConnectionException) as e:
            logger.error(e, exc_info=True)
            raise HTTPException(
                status_code=http.HTTPStatus.SERVICE_UNAVAILABLE,
                detail="service temporarily unavailable"
            )

        except (IMAPCommandException, SMTPCommandException) as e:
            logger.error(e, exc_info=True)
            raise HTTPException(
                status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="command error"
            )

        except (IMAPAuthenticationException, SMTPAuthenticationException) as e:
            logger.error(e, exc_info=True)
            raise HTTPException(
                status_code=http.HTTPStatus.UNAUTHORIZED,
                detail="authenticated failed"
            )

        except Exception as e:
            logger.error(e, exc_info=True)
            raise HTTPException(
                status_code=http.HTTPStatus.SERVICE_UNAVAILABLE,
                detail="service temporarily unavailable"
            )

    return decorator
