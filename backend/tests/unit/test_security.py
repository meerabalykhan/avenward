from app.security import hash_password, new_session_token, token_digest, verify_password


def test_password_hashes_are_salted_and_verifiable() -> None:
    first = hash_password("a sufficiently long password")
    second = hash_password("a sufficiently long password")
    assert first != second
    assert verify_password("a sufficiently long password", first)
    assert not verify_password("the wrong password", first)
    assert not verify_password("anything", "broken")


def test_session_tokens_store_only_a_digest() -> None:
    token, digest = new_session_token()
    assert token not in digest
    assert digest == token_digest(token)
