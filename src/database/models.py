from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Telegram ID лучше делать BigInteger, так как ID пользователей в Telegram крупные
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[Optional[str]] = mapped_column(String(64))  # Optional = может быть NULL
    username: Mapped[Optional[str]] = mapped_column(String(32))
    
    # func.now() автоматически подставит текущую дату/время Postgres при создании
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Связь "один-ко-многим": один пользователь может иметь много записей
    records: Mapped[list["HeadacheRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class HeadacheRecord(Base):
    __tablename__ = "headache_records"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    pain_date: Mapped[date]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    is_pain: Mapped[bool] = mapped_column(default=True)
    medicine: Mapped[Optional[str]] = mapped_column(String(64))
    comment: Mapped[Optional[str]] = mapped_column(String(512))

    # Обратная связь к пользователю
    user: Mapped["User"] = relationship(back_populates="records")