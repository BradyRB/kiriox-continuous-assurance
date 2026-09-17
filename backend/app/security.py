import base64
import hashlib
import logging
from cryptography.fernet import Fernet
from .config import get_settings

class SecretBox:
    """Encrypts credentials using a master key that is never stored in PostgreSQL."""
    def __init__(self, master_key: str):
        self._fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(master_key.encode()).digest()))
    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode()).decode()
    def decrypt(self, value: str) -> str:
        return self._fernet.decrypt(value.encode()).decode()

class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        text = str(record.getMessage())
        for marker in ("password", "token", "secret", "authorization"):
            text = text.replace(marker, f"{marker[:1]}***")
        record.msg, record.args = text, ()
        return True

secret_box = SecretBox(get_settings().kiriox_master_key)
