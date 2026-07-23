"""Password and opaque-session primitives using the Python standard library."""

import hashlib
import hmac
import secrets


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Hash a password with scrypt and a random salt."""

    actual_salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=actual_salt, n=2**14, r=8, p=1)
    return f"scrypt${actual_salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Constant-time verification of an encoded scrypt password."""

    try:
        algorithm, salt_hex, expected = encoded.split("$", 2)
        if algorithm != "scrypt":
            return False
        candidate = hash_password(password, bytes.fromhex(salt_hex)).split("$", 2)[2]
        return hmac.compare_digest(candidate, expected)
    except (ValueError, TypeError):
        return False


def new_session_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    return token, token_digest(token)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode(), usedforsecurity=False).hexdigest()
