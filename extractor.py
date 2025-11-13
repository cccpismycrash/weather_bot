from tenacity import retry, stop_after_delay, wait_fixed
from httpx import AsyncClient, QueryParams, Response


class Extractor():

    def __init__(self) -> None:
        self._http_client = AsyncClient()
        self.__api_key = None


    def set_api(self, 
                api_key: str) -> None:
        
        """
        Set API key to worker. Without API key worker won't work.

        """

        self.__api_key = api_key


    @retry(wait=wait_fixed(5), stop=stop_after_delay(10), reraise=True)
    async def _request(self, url: str, params: QueryParams | None = None) -> Response:
        response = await self._http_client.get(url, params=params)
        return response


    async def get_coord(self, 
                        city_name: str) -> tuple[str, float, float]:

        """
        Returns a tuple of name of the city [ru], latitude and longtitude. Set API key before calling this function.

        """

        url = f"http://api.openweathermap.org/geo/1.0/direct"
        
        params = {
            'q': str(city_name), 
            'appid': str(self.__api_key)
            }

        http = await self._request(url, params)

        data = http.json()

        local_name = data[0]["local_names"]["ru"]
        lat = data[0]["lat"]
        lon = data[0]["lon"]

        return local_name, lat, lon


    async def get_temp(self, 
                       lat: int, 
                       lon: int) -> float:

        """
        Returns a temperature at the certain location. Set API key before calling this function.

        """

        url = f"https://api.openweathermap.org/data/2.5/weather"
        
        params = {
            'lat':str(lat), 
            'lon': str(lon), 
            'lang': 'ru',
            'appid': str(self.__api_key)
            }

        http = await self._request(url, params)

        data = http.json()

        temp = data["main"]["temp"]

        return round(temp - 273.15, 1)
    

    async def get_temp_with_city_name(self, 
                            lat: int, 
                            lon: int
                            ) -> tuple[float, str]:

        """
        Returns a tuple of temp in a certain city and city name [en]. Set API key before calling this function.

        """

        url = f"https://api.openweathermap.org/data/2.5/weather"
        
        params = {
            'lat':str(lat), 
            'lon': str(lon), 
            'appid': str(self.__api_key)
            }

        http = await self._request(url, params)

        data = http.json()

        city_name = data["name"]
        temp = data["main"]["temp"]

        return temp, city_name