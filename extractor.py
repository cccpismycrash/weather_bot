from tenacity import retry, stop_after_delay, wait_fixed
from httpx import Client, QueryParams, Response

class Extractor():
    def __init__(self):
        self._http_client = Client()
        self.__api_key = None

    def set_api(self, api_key):
        self.__api_key = api_key

    @retry(wait=wait_fixed(5), stop=stop_after_delay(10), reraise=True)
    def _request(self, url: str, params: QueryParams | None = None) -> Response:
        response = self._http_client.get(url, params=params)
        return response

    def get_temp(self, lat, lon):

        url = f"https://api.openweathermap.org/data/2.5/weather"
        
        params = {
            'lat':str(lat), 
            'lon': str(lon), 
            'appid': str(self.__api_key)
            }

        http = self._request(url, params)

        data = http.json()

        temp = data["main"]["temp"]

        return round(temp - 273.15, 1)