import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

_key = os.getenv("ENCRYPTION_KEY")
if not _key:
    raise RuntimeError("ENCRYPTION_KEY is not set in .env")

_fernet = Fernet(_key.encode())


def encrypt_token(plain_text: str) -> str:
    return _fernet.encrypt(plain_text.encode()).decode()


def decrypt_token(encrypted_text: str) -> str:
    return _fernet.decrypt(encrypted_text.encode()).decode()