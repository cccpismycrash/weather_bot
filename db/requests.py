from typing import Optional
from sqlalchemy import select, update, delete

import logging

from db.models import async_session
from db.models import Users, Cities, Relation


async def add_user(telegram_id: int, 
                   latitude: int, 
                   longitude: int
                   ) -> None:

    """
    Add a new user in "Users" table

    """

    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            await session.execute(
                update(Users)
                .where(Users.telegram_id == telegram_id)
                .values(latitude=latitude, 
                        longitude=longitude)
            )
        else:
            session.add(Users(
                telegram_id=telegram_id,
                latitude=latitude,
                longitude=longitude
            ))

        logging.info("User was added")

        await session.commit()


async def get_coordinate(telegram_id: int) -> tuple[Optional[float], Optional[float]]:

    """
    Returns a tuple: (latitude, longitude)

    """

    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logging.warning("Coordinates weren't received")
            return None, None
        else:
            latitude = user.latitude
            longitude = user.longitude
            logging.info("Coordinates were received")
            return latitude, longitude


async def get_notification_config_for_user(telegram_id: int) -> tuple[Optional[str], Optional[Users]]:

    """
    Returns a tuple: (string, User) 

    """

    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logging.warning("Config wasn't received")
            return _answer_notification(None), None
        else:
            logging.info("Config was received")
            return _answer_notification(user), user
    

def _answer_notification(user: Users) -> str:
    if not user:
        return "У вас нет заготовленных уведомлений."
    else:
        latitude = user.latitude
        longitude = user.longitude

        freq = user.frequency

        match freq:
            case 1:
                freq_text = "за 30 минут."
            case 2:
                freq_text = "за час."
            case 4:
                freq_text = "за 2 часа."
            case 8:
                freq_text = "за 4 часа."
            case 16:
                freq_text = "за 8 часов."
            case 48:
                freq_text = "за 24 часа."
            case _:
                freq_text = "Error"

        diff_text = f'*{user.diff_temp}°C* ' + freq_text

        # Users - Cities as M-N relation

        notifications: str = []

        for relation in user.relations_of_users:
            if relation.to_city and relation.to_city.city_name_ru:
                notifications.append(f'*{relation.to_city.city_name_ru.capitalize()}:* {diff_text}')

        answer = []

        answer.append(
            f"Ваши координаты:\n\n"
            f"_Широта:_ {latitude}\n"
            f"_Долгота:_ {longitude}\n\n"
            f"Настройки уведомлений:"
        )

        for i in notifications:
            answer.append(f"{i}")

        answer.append("-------")

        return "\n\n".join(answer)


async def delete_user_data(telegram_id: int) -> None:

    """
    Delete a relations and user data of certain user 

    """

    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logging.warning("Relations and user data of user weren't deleted")
            return

        await session.execute(
            delete(Relation).where(Relation.user_id == user.user_id)
        )

        await session.execute(
            delete(Users).where(Users.user_id == user.user_id)
        )
        logging.info("Relations and user data of user were deleted")

        await session.commit()
        return


async def delete_user_relations(telegram_id: int) -> None:

    """
    Delete a relations of certain user 

    """

    async with async_session() as session:
        result = await session.execute(
            select(Users).where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logging.warning("Relations of user weren't deleted")
            return

        await session.execute(
            delete(Relation).where(Relation.user_id == user.user_id)
        )

        logging.info("Relations of user were deleted")

        await session.commit()
        return

async def get_city_data(city_id: int) -> dict[str, str | float]:

    """
    Returns a dict with data of certain city

    """

    async with async_session() as session:
        result = await session.execute(
            select(Cities)
            .where(Cities.city_id == city_id)
        )
        city = result.scalar_one_or_none()
    
    res_dict = {
        'city_name': city.city_name, 
        'city_name_ru': city.city_name_ru,
        'latitude': city.latitude,
        'longitude': city.longitude,
    }

    logging.info("City data were recieved")

    return res_dict    


async def get_users_id() -> list[int]:

    """
    Returns a list with the telegram IDs for all users

    """

    async with async_session() as session:
        result = await session.execute(
            select(Users.telegram_id)
        )
        users = result.scalars().all()

        logging.info("Users id were recieved")

        return users


async def set_config(telegram_id: int, 
                     frequency: int, 
                     diff_temp: float, 
                     users_temp: float, 
                     city_name: str
                     ) -> None:
    
    """
    Update attributes of existing certain user in "Users" table.
    Also add relation between Users entity and Cities entity in "Relation" table. 

    """
    
    async with async_session() as session:
        result = await session.execute(
            update(Users)
            .where(Users.telegram_id == telegram_id)
            .values(frequency=frequency, 
                    diff_temp=diff_temp, 
                    users_temp=users_temp)
            .returning(Users.user_id)
        )

        result_city = await session.execute(
            select(Cities)
            .where(Cities.city_name == city_name)
        )

        city = result_city.scalar_one_or_none()

        if city is None:
            new_city = Cities(city_name=city_name)
            session.add(new_city)
            await session.flush()
            city_id = new_city.city_id
        else:
            city_id = city.city_id
        
        user_id = result.scalar_one_or_none()

        session.add(Relation(
            user_id=user_id,
            city_id=city_id,
        ))
        await session.commit()

        logging.info("Config was set")


async def get_user_attrs(telegram_id: int) -> dict[str, int | float]:

    """
    Returns a dict with attributes of certain user

    """

    async with async_session() as session:
        result = await session.execute(
            select(Users)
            .where(Users.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        res_dict = {

            'user_id': user.user_id,
            'telegram_id': user.telegram_id, 
            'latitude': user.latitude,
            'longitude': user.longitude,
            'frequency': user.frequency,
            'diff_temp': user.diff_temp,
            'users_temp': user.users_temp,
            'counter': user.counter,

        }
        
        logging.info("User attributes were recieved")

        return res_dict


async def update_city_data(city_name: str, 
                           city_name_ru: str, 
                           latitude: float, 
                           longitude: float,
                           city_temp: float
                           ) -> None:

    """
    Update a data of certain city

    """

    async with async_session() as session:
        await session.execute(
            update(Cities)
            .where(Cities.city_name == city_name)
            .values(city_name_ru=city_name_ru,
                    latitude=latitude, 
                    longitude=longitude,
                    temp=city_temp)
        )

        await session.commit()

        logging.info("City data were updated")
        

async def get_city_temp(city_id: int) -> None:

    """
    Returns the temperature of certain city

    """

    async with async_session() as session:
        result = await session.execute(
            select(Cities)
            .where(Cities.city_id == city_id)
            )

        city = result.scalar_one_or_none()

        logging.info("City temp was recieved")

    return city.temp


async def update_user_counter(telegram_id: int, 
                              counter: int
                              ) -> None:

    """
    Update a counter of certain user

    """

    async with async_session() as session:
        await session.execute(
            update(Users)
            .where(Users.telegram_id == telegram_id)
            .values(counter=counter)
        )
    
        await session.commit()

        logging.info("User counter was updated")


async def update_user_temp(telegram_id: int, 
                           users_temp: float
                           ) -> None:

    """
    Update a user's temp of certain user

    """

    async with async_session() as session:
        await session.execute(
            update(Users)
            .where(Users.telegram_id == telegram_id)
            .values(users_temp=users_temp)
        )
    
        await session.commit()

        logging.info("User temp was updated")


async def update_city_temp(city_id: int, 
                           temp: float
                           ) -> None:

    """
    Update a city temp of certain city

    """

    async with async_session() as session:
        await session.execute(
            update(Cities)
            .where(Cities.city_id == city_id)
            .values(temp=temp)
        )
    
        await session.commit()

        logging.info("City temp were updated")


async def get_cities_id() -> list[tuple[int, str]]:

    """
    Returns a list of tuples with the city IDs for all cities and the city name: (city_id, city_name)

    """

    async with async_session() as session:
        result = await session.execute(
            select(Cities.city_id, Cities.city_name)
        )
        cities = result.all()

        logging.info("Cities id were recieved")

        return cities


async def get_city_subscribers_id(city_id: int) -> list[int]:

    """
    Returns a list with the user IDs of subscribers of certain city

    """
    async with async_session() as session:
        result = await session.execute(
            select(Users.telegram_id)
            .join(Relation, Relation.user_id == Users.user_id)
            .join(Cities, Cities.city_id == Relation.city_id)
            .where(Cities.city_id == city_id)
        )
        telegram_ids = result.scalars().all()

        logging.info("City subscribers were recieved")

        return telegram_ids