import datetime as dt

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String(100), nullable=False)

    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash = Column(
        String(500),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=dt.datetime.utcnow,
        nullable=False,
    )

    analyses = relationship(
        "AnalysisResult",
        back_populates="user",
        cascade="all, delete-orphan",
    )