from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import Integer, BigInteger, Float, UniqueConstraint, ForeignKey, DateTime, Time
from datetime import datetime

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite')
async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    relations_of_users = relationship("Relation", back_populates="to_users", lazy="selectin")

class Schedule(Base):
    __tablename__ = "schedule"

    schedule_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    time: Mapped[datetime.time] = mapped_column(Time, unique=True)

    relations_of_schedule = relationship("Relation", back_populates="to_schedule", lazy="selectin")

class Relation(Base):
    __tablename__ = "relation"

    relation_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"))
    schedule_id: Mapped[int] = mapped_column(Integer, ForeignKey("schedule.schedule_id"))

    __table_args__ = (
        UniqueConstraint("user_id", "schedule_id", name="uq_relation_user_schedule"),
    )

    to_users = relationship("Users", back_populates="relations_of_users", lazy="selectin")
    to_schedule = relationship("Schedule", back_populates="relations_of_schedule", lazy="selectin")

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)