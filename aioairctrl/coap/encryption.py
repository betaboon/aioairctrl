import hashlib

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad


class DigestMismatchException(Exception):
    pass


class EncryptionContext:
    SECRET_KEY = "JiangPan"

    def __init__(self):
        self._client_key = None

    def set_client_key(self, client_key):
        self._client_key = client_key

    def _increment_client_key(self):
        client_key_next = (int(self._client_key, 16) + 1).to_bytes(4, byteorder="big").hex().upper()
        self._client_key = client_key_next

    def _create_cipher(self, key: str):
        key_and_iv = hashlib.md5((self.SECRET_KEY + key).encode()).hexdigest().upper()
        half_keylen = len(key_and_iv) // 2
        secret_key = key_and_iv[0:half_keylen]
        iv = key_and_iv[half_keylen:]
        cipher = AES.new(
            key=secret_key.encode(),
            mode=AES.MODE_CBC,
            iv=iv.encode(),
        )
        return cipher

    def encrypt(self, payload: str) -> str:
        self._increment_client_key()
        key = self._client_key
        plaintext_padded = pad(payload.encode(), 16, style="pkcs7")
        cipher = self._create_cipher(key)
        ciphertext = cipher.encrypt(plaintext_padded).hex().upper()
        digest = hashlib.sha256((key + ciphertext).encode()).hexdigest().upper()
        return key + ciphertext + digest

    def decrypt(self, payload_encrypted: str) -> str:
        key = payload_encrypted[0:8]
        ciphertext = payload_encrypted[8:-64]
        digest = payload_encrypted[-64:]
        digest_calculated = hashlib.sha256((key + ciphertext).encode()).hexdigest().upper()
        if digest != digest_calculated:
            raise DigestMismatchException
        cipher = self._create_cipher(key)
        plaintext_padded = cipher.decrypt(bytes.fromhex(ciphertext))
        plaintext_unpadded = unpad(plaintext_padded, 16, style="pkcs7")
        return plaintext_unpadded.decode()
