"""Application-layer encryption and keyed equality indexes; keys live outside the DB."""
import hashlib
import hmac
import json
import os
from cryptography.fernet import Fernet, MultiFernet
from sqlalchemy import JSON, Text
from sqlalchemy.types import TypeDecorator

PREFIX = 'enc:v1:'

def cipher():
    keys = os.environ.get('PII_ENCRYPTION_KEYS', '').split(',')
    if not keys[0]:
        raise RuntimeError('PII_ENCRYPTION_KEYS must be configured before storing personal data')
    return MultiFernet([Fernet(key.strip().encode()) for key in keys])

def encrypt(value):
    return PREFIX + cipher().encrypt(value.encode()).decode()

def decrypt(value):
    # Legacy reads exist only to permit an online backfill; every new write encrypts.
    return cipher().decrypt(value[len(PREFIX):].encode()).decode() if value.startswith(PREFIX) else value

def lookup(value, purpose='email'):
    key = os.environ.get('PII_LOOKUP_KEY', '')
    if len(key) < 32:
        raise RuntimeError('PII_LOOKUP_KEY must be a separate random secret of at least 32 characters')
    return hmac.new(key.encode(), f'{purpose}:{value.strip().lower()}'.encode(), hashlib.sha256).hexdigest()

class PrivateText(TypeDecorator):
    impl = Text
    cache_ok = True
    def process_bind_param(self, value, dialect):
        return encrypt(value) if value is not None else None
    def process_result_value(self, value, dialect):
        return decrypt(value) if value is not None else None

class PrivateJSON(TypeDecorator):
    impl = JSON
    cache_ok = True
    def process_bind_param(self, value, dialect):
        return {'encrypted_v1': encrypt(json.dumps(value, ensure_ascii=False))} if value is not None else None
    def process_result_value(self, value, dialect):
        return json.loads(decrypt(value['encrypted_v1'])) if isinstance(value, dict) and 'encrypted_v1' in value else value
