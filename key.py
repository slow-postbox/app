def get() -> str:
    try:
        with open(".KEY_STORE", mode="rb") as reader:
            return reader.read().hex()
    except FileNotFoundError:
        return write()


def write() -> str:
    token = input("TOKEN=")
    tk_bytes = bytes.fromhex(token)

    with open(".KEY_STORE", mode="wb") as writer:
        writer.write(tk_bytes)

    print("* NEW TOKEN SAVED *")
    return token


if __name__ == "__main__":
    write()
