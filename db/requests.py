from datetime import datetime, time
from db.models import async_session
from db.models import Users, Schedule, Relation
from sqlalchemy import select, and_, func, update, delete

async def add_user(telegram_id, latitude, longitude):
    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            await session.execute(
                update(Users)
                .where(Users.telegram_id == telegram_id)
                .values(latitude=latitude, longitude=longitude)
            )
        else:
            session.add(Users(
                telegram_id=telegram_id,
                latitude=latitude,
                longitude=longitude
            ))

        await session.commit()


async def add_schedule_for_user(telegram_id, hour, minute):
    async with async_session() as session:

        result = await session.execute(
            select(Users).where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"Пользователь с telegram_id={telegram_id} не найден")

        schedule_time = time(hour=hour, minute=minute)

        result = await session.execute(
            select(Schedule).where(Schedule.time == schedule_time)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            schedule_ = Schedule(time=schedule_time)
            session.add(schedule_)
            await session.flush()

            relation = Relation(
                user_id=user.user_id,
                schedule_id=schedule_.schedule_id
            )
            session.add(relation)
        else:
            relation = Relation(
                user_id=user.user_id,
                schedule_id=schedule.schedule_id
            )
            session.add(relation)

        await session.commit()

async def get_coordinate(telegram_id):
    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None, None
        else:
            latitude = user.latitude
            longitude = user.longitude
            return latitude, longitude

async def get_schedule_for_user(telegram_id):
    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return answerSchedule(None), None
        else:
            return answerSchedule(user), user
    
def answerSchedule(user):
    if not user:
        return "У вас нет расписания."
    else:
        latitude = user.latitude
        longitude = user.longitude

        schedule_times = []
        for relation in user.relations_of_users:
            if relation.to_schedule and relation.to_schedule.time:
                schedule_times.append(relation.to_schedule.time.strftime("%H:%M"))

        schedule_times.sort()

        answer = []

        answer.append(
            f"""Ваши координаты:

Широта: {latitude}
Долгота: {longitude}

Время уведомлений:
"""
        )

        for i in schedule_times:
            answer.append(f"{i}\n")

        answer.append("-------")

        return "\n\n".join(answer)

async def get_schedule(telegram_id) -> dict | None:
    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return listSchedule(None)
        else:
            return listSchedule(user)    

def listSchedule(user) -> dict | None:
    if not user:
        return None
    else:
        latitude = user.latitude
        longitude = user.longitude

        schedule_times = []
        for relation in user.relations_of_users:
            if relation.to_schedule and relation.to_schedule.time:
                schedule_times.append(relation.to_schedule.time)

        schedule_times.sort()

        res = {
            "latitude": latitude,
            "longitude": longitude,
            "schedule": schedule_times,
        }

        return res

async def delete_user_relations(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False

        await session.execute(
            delete(Relation).where(Relation.user_id == user.user_id)
        )

        await session.delete(user)

        await session.commit()
        return True

async def get_users():
    async with async_session() as session:
        result = await session.execute(
            select(Users.telegram_id)
        )
        users = result.scalars().all()
        return users