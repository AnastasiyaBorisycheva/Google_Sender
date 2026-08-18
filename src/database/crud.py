from typing import Optional
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, HeadacheRecord

async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    username: Optional[str] = None
) -> User:

    user_request = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(user_request)
    user = result.scalar_one_or_none()

    if user:
        updated = False

        if first_name is not None and user.first_name != first_name:
            user.first_name = first_name
            updated = True

        if last_name is not None and user.last_name != last_name:
            user.last_name = last_name
            updated = True

        if username is not None and user.username != username:
            user.username = username
            updated = True

        if updated:
            await session.commit()

    else:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )
        session.add(user)
        await session.commit()

    await session.refresh(user)
    return user

async def add_headache_record(
    session: AsyncSession,
    user_id: int,
    pain_date: date,
    is_pain: bool = True,
    medicine: Optional[str] = None,
    comment: Optional[str] = None
) -> HeadacheRecord:

    pain_request = select(HeadacheRecord).where(
        HeadacheRecord.user_id == user_id,
        HeadacheRecord.pain_date == pain_date
    )

    result = await session.execute(pain_request)

    headache_record = result.scalar_one_or_none()    

    if headache_record:
        if (
            headache_record.is_pain != is_pain
            or headache_record.medicine != medicine
            or headache_record.comment != comment
        ):
            headache_record.is_pain = is_pain
            headache_record.medicine = medicine
            headache_record.comment = comment
            await session.commit()
    else:
        headache_record = HeadacheRecord(
            user_id = user_id,
            pain_date = pain_date,
            is_pain = is_pain,
            medicine = medicine,
            comment = comment
        )
        session.add(headache_record)
        await session.commit()

    await session.refresh(headache_record)
    return headache_record