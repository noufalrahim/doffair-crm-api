from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt has a 72 byte limit, truncate if necessary
    truncated_password = plain_password[:72] if len(plain_password) > 72 else plain_password
    return pwd_context.verify(truncated_password, hashed_password)
