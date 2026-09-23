from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(
    db: Session,
    name: str,
    email: str,
    password: str,
) -> User:

    email = normalize_email(email)

    existing = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing:
        raise ValueError(
            "An account with this email already exists."
        )

    user = User(
        name=name.strip(),
        email=email,
        password_hash=hash_password(password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:

    email = normalize_email(email)

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def create_user_token(user: User) -> str:
    return create_access_token(user.id)