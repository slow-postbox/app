from collections import namedtuple

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad
from Crypto.Random import get_random_bytes

from app import db
from app.models import KeyStore

Key = namedtuple("Key", ['key', 'iv'])


def encrypt(key_store: Key, content: str) -> bytes:
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


def decrypt(key_store: Key, result: bytes) -> str:
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
    key_store = KeyStore.query.filter_by(
        owner_id=owner_id,
        mail_id=mail_id
    ).first()

    if key_store is None:
        key_store = KeyStore()
        key_store.owner_id = owner_id
        key_store.mail_id = mail_id
        key_store.key = get_random_bytes(32).hex()
        key_store.iv = get_random_bytes(16).hex()

        db.session.add(key_store)
        db.session.commit()

    return encrypt(
        key_store=Key(
            key=bytes.fromhex(key_store.key),
            iv=bytes.fromhex(key_store.iv)
        ),
        content=content
    ).hex()


def decrypt_mail(owner_id: int, mail_id: int, result: str) -> str:
    key_store = KeyStore.query.filter_by(
        owner_id=owner_id,
        mail_id=mail_id
    ).first()

    if key_store is None:
        raise Exception("FAIL TO GET KEY STORE")

    return decrypt(
        key_store=Key(
            key=bytes.fromhex(key_store.key),
            iv=bytes.fromhex(key_store.iv)
        ),
        result=bytes.fromhex(result)
    )
