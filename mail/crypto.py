from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad

from mail.utils import KeyStore
from mail.utils import fetch_key_store


def encrypt(key_store: KeyStore, content: str) -> bytes:
    cipher = AES.new(
        key=key_store.key,
        iv=key_store.iv,
        mode=AES.MODE_CBC,
    )

    return cipher.encrypt(
        plaintext=pad(
            data_to_pad=content.encode("utf-8"),
            block_size=AES.block_size,
            style="pkcs7"
        )
    )


def decrypt(key_store: KeyStore, result: bytes) -> str:
    cipher = AES.new(
        key=key_store.key,
        mode=AES.MODE_CBC,
        iv=key_store.iv
    )

    return unpad(
        padded_data=cipher.decrypt(result),
        block_size=AES.block_size,
        style="pkcs7"
    ).decode("utf-8")


def encrypt_mail(owner_id: int, mail_id: int, content: str) -> str:
    key_store = fetch_key_store(
        owner_id=owner_id,
        mail_id=mail_id
    )

    return encrypt(
        key_store=key_store,
        content=content
    ).hex()


def decrypt_mail(owner_id: int, mail_id: int, result: str) -> str:
    key_store = fetch_key_store(
        owner_id=owner_id,
        mail_id=mail_id
    )

    return decrypt(
        key_store=key_store,
        result=bytes.fromhex(result)
    )
