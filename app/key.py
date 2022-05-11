from secrets import token_bytes

FILE_NAME = ".SECRET_KEY"
LENGTH = 32


def secret_key() -> bytes:
    try:
        with open(FILE_NAME, mode="rb") as reader:
            key = reader.read()

        if len(key) != LENGTH:
            raise ValueError
    except (FileNotFoundError, ValueError):
        key = token_bytes(LENGTH)
        with open(FILE_NAME, mode="wb") as writer:
            writer.write(key)

    return key

