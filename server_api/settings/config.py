import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server_api.settings import middleware

app = FastAPI()

# adding middleware
app.middleware("http")(middleware.parse_auth_token)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# adding setting
env = dict()

# imap settings
env["IMAP_SETTINGS"] = {
    "host": os.environ.get("ADAPTER_IMAP_HOST", "localhost"),
    "port": os.environ.get("ADAPTER_IMAP_PORT", 143),
}

env["IMAP_MASTER_SETTINGS"] = {
    "host": os.environ.get("ADAPTER_IMAP_MASTER_HOST", "localhost"),
    "port": os.environ.get("ADAPTER_IMAP_MASTER_PORT", 143),
}

# smtp settings
env["SMTP_SETTINGS"] = {
    "host": os.environ.get("ADAPTER_SMTP_HOST", "localhost"),
    "port": os.environ.get("ADAPTER_SMTP_PORT", 25),
}

env["MASTER_SETTINGS"] = {
    "username": os.environ.get("ADAPTER_MASTER_USERNAME", "master"),
    "password": os.environ.get("ADAPTER_MASTER_PASSWORD", "secret"),
}

env["SIEVE_SETTINGS"] = {
    "host": os.environ.get("ADAPTER_IMAP_MASTER_HOST", "localhost"),
    "port": os.environ.get("ADAPTER_SIEVE_PORT", 4190)
}
