"""Password hashing guarantees for the direct-bcrypt implementation.

``app.services.auth_service`` used to hash through passlib. It now calls
``bcrypt`` directly, because passlib 1.7.4 is unmaintained and was the only
reason bcrypt had to be pinned below 4.1. These tests pin the properties that
make the swap safe:

1. a hash produced by the old passlib code still verifies, so no stored
   credential is orphaned;
2. bcrypt's 72-byte truncation behaviour is unchanged;
3. a malformed hash fails the login instead of raising.

Run with:
    python -m pytest test_password_hashing.py -q
"""
from __future__ import annotations

import pytest

from app.services.auth_service import get_password_hash, verify_password

# Real output of passlib 1.7.4 (CryptContext(["bcrypt"]), default rounds=12)
# backed by bcrypt 4.0.1 -- i.e. the exact implementation that was replaced.
# The plaintext is PASSLIB_PASSWORD.
PASSLIB_HASH = "$2b$12$sBgXvmg5g6sYaJGzOk/CMuydxTHwvwyVi8GRocyvjI3l4r1pcjUXm"
PASSLIB_PASSWORD = "pass12345"


def test_passlib_generated_hash_still_verifies():
    """A credential written before the swap must still authenticate."""
    assert verify_password(PASSLIB_PASSWORD, PASSLIB_HASH) is True


def test_passlib_generated_hash_rejects_wrong_password():
    assert verify_password(PASSLIB_PASSWORD + "x", PASSLIB_HASH) is False


def test_hash_round_trip_and_format():
    hashed = get_password_hash("correct horse battery staple")
    assert hashed.startswith("$2b$12$")
    assert len(hashed) == 60
    assert verify_password("correct horse battery staple", hashed) is True
    assert verify_password("correct horse battery stapl", hashed) is False


def test_each_hash_uses_a_fresh_salt():
    assert get_password_hash("same-password") != get_password_hash("same-password")


def test_password_longer_than_72_bytes_is_truncated_not_rejected():
    """bcrypt ignores bytes past 72. Truncating must match passlib's silent
    truncation and must not raise (newer bcrypt releases raise on >72 bytes)."""
    long_password = "A" * 100
    hashed = get_password_hash(long_password)
    assert verify_password(long_password, hashed) is True
    assert verify_password("A" * 72, hashed) is True


def test_non_ascii_password_round_trips():
    hashed = get_password_hash("密码-päss-🔐")
    assert verify_password("密码-päss-🔐", hashed) is True


@pytest.mark.parametrize(
    "bad_hash",
    [
        "",
        "not-a-hash",
        "$1$md5$abcdefghijklmnopqrstuv",
        # The next two are the important ones. Measured against bcrypt 4.2.1 they
        # make the Rust extension panic with an exception that is catchable
        # neither as ValueError nor as Exception, so verify_password has to reject
        # them by format before the extension is ever called.
        "$2b$12$tooshort",
        "$2a$10$short",
        "$2b$12$" + "a" * 52,  # one character short of a well-formed hash
        "$2b$99$" + "a" * 53,  # cost outside bcrypt's legal 04-31 range
        "$2b$03$" + "a" * 53,  # cost below bcrypt's legal range
        "$2b$12$" + "!" * 53,  # illegal character in the base64 body
    ],
)
def test_malformed_hash_fails_closed(bad_hash):
    """A corrupt row must produce a failed login, never an exception."""
    assert verify_password("whatever", bad_hash) is False


def test_empty_password_fails_closed():
    assert verify_password("", get_password_hash("x")) is False
