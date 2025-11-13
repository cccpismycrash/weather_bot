from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import Integer, BigInteger, Float, UniqueConstraint, ForeignKey, String


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
    frequency: Mapped[int] = mapped_column(Integer, nullable=True)
    diff_temp: Mapped[float] = mapped_column(Float, nullable=True)
    users_temp: Mapped[float] = mapped_column(Float, nullable=True)
    counter: Mapped[int] = mapped_column(Integer, nullable=True)

    relations_of_users = relationship("Relation", back_populates="to_user", lazy="selectin")


class Relation(Base):
    __tablename__ = "relation"

    relation_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"))
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey("cities.city_id"))

    __table_args__ = (
        UniqueConstraint("user_id", "city_id", name="uq_relation_config_city"),
    )

    to_user = relationship("Users", back_populates="relations_of_users", lazy="selectin")
    to_city = relationship("Cities", back_populates="relations_of_cities", lazy="selectin")


class Cities(Base):
    __tablename__ = "cities"

    city_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    city_name: Mapped[str] = mapped_column(String)
    city_name_ru: Mapped[str] = mapped_column(String, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    temp: Mapped[float] = mapped_column(Float, nullable=True)

    relations_of_cities = relationship("Relation", back_populates="to_city", lazy="selectin")


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)