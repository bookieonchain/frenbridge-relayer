import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Keystore:
    def __init__(self, key):
        self.fernet = Fernet(key)

    @classmethod
    def from_file(cls, filepath: str, password: bytes):
        with open(filepath, "rb") as f:
            salt = f.read()
            print("saltt", salt)
            key = cls.create_key(salt, password)

    @staticmethod
    def create_key(salt: bytes, password: bytes):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))

    @classmethod
    def create_keystore(cls, password: bytes, salt_file: Optional[str] = None):
        salt = os.urandom(16)
        with open(salt_file, "wb") as f:
            f.write(salt)
        print("salt", salt)
        key = cls.create_key(salt, password)
        return cls(key)

    def encrypt(self, msg: bytes):
        return self.fernet.encrypt(msg)

    def decrypt(self, msg: bytes):
        return self.fernet.decrypt(msg)


if __name__ == "__main__":
    k = Keystore.create_keystore(b"test123", "keystore.key")
    encrypted = k.encrypt(b"ABC123")
    k = Keystore.from_file("keystore.key", b"test123")
    print(k.decrypt(encrypted))
