import re
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models import User
from ..config import SECRET_KEY, ALGORITHM

# bcrypt consumes only the first 72 bytes of a password, and newer releases raise
# on longer input. Truncating here reproduces the behaviour of the passlib-based
# implementation this replaces (passlib 1.7.4 truncated silently), so password
# length semantics are unchanged.
_BCRYPT_MAX_BYTES = 72
_BCRYPT_ROUNDS = 12

# A bcrypt hash is exactly 60 characters: "$2<rev>$<cost>$" plus 53 characters of
# bcrypt's base64 alphabet. The cost must be in bcrypt's legal 04-31 range.
_BCRYPT_HASH_RE = re.compile(r"^\$2[abxy]\$(?:0[4-9]|[12]\d|3[01])\$[./A-Za-z0-9]{53}$")

def _password_bytes(password: str) -> bytes:
    return (password or "").encode("utf-8")[:_BCRYPT_MAX_BYTES]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    if not _BCRYPT_HASH_RE.match(hashed_password):
        # This format check is the real defence, not the try/except below.
        # bcrypt 4.1+ is a Rust extension and does not merely raise on a malformed
        # hash: measured against bcrypt 4.2.1, a "$2b$"-prefixed string that is too
        # short makes it panic inside Rust, raising pyo3_runtime.PanicException.
        # That type derives from BaseException, so "except Exception" never sees
        # it, and "pyo3_runtime" is not an importable module, so the class cannot
        # be named in an except clause either. Refusing anything that is not a
        # well-formed bcrypt hash keeps such input out of the extension entirely,
        # which is the only guard that actually holds. (Strings without the "$2"
        # prefix raise ValueError, and an out-of-range cost does too, so those
        # paths are already safe.)
        return False
    try:
        return bcrypt.checkpw(
            _password_bytes(plain_password), hashed_password.encode("utf-8")
        )
    except ValueError:
        # The C extension in bcrypt <= 4.0 reports a bad hash as ValueError.
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        _password_bytes(password), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    ).decode("utf-8")

def get_user(db: Session, username: str) -> Optional[User]:
    normalized = username.strip().lower()
    return db.query(User).filter(func.lower(User.username) == normalized).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.strip().lower()).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user(db, username)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def register_user(db: Session, username: str, email: str, password: str) -> User:
    hashed_password = get_password_hash(password)
    user = User(username=username.strip().lower(), email=email.strip().lower(), hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user