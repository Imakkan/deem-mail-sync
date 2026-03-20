import json
import base64
import logging
import re


from fastapi import Request
from fastapi import FastAPI

app = FastAPI()
logger = logging.getLogger(__name__)


async def parse_auth_token(request: Request, call_next):

    def _correct_token_padding(token):
        token += '=' * (-len(token) % 4)
        return token

    def _get_user(token):
        correct_token = _correct_token_padding(token.split(".")[1])
        decoded_token = json.loads(base64.b64decode(correct_token))
        return {
            "email": decoded_token["email"],
            "name": decoded_token["name"]
        }

    def _get_user_from_master(token):
        return {"email": base64.b64decode(token).decode()}

    def _get_sasl_token(user, token):
        return "user=%s\x01auth=Bearer %s\x01\x01" % (user, token)

    auth_token = request.headers["Authorization"].split(" ")[1]
    if re.match('^/master', request.url.path):
        request.state.mail_user = _get_user_from_master(auth_token)
    else:
        request.state.mail_user = _get_user(auth_token)
        request.state.mail_sasl_token = _get_sasl_token(request.state.mail_user["email"], auth_token)
    return await call_next(request)
