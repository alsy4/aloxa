import requests

from config import WEATHER_API_KEY, WEATHER_API_URL, WEATHER_DEFAULT_LOCATION


class WeatherClient:
    """Fetches weather data from weatherapi.com."""

    def __init__(self, location: str | None = None):
        self.location = location or WEATHER_DEFAULT_LOCATION
        self._api_key = WEATHER_API_KEY

    def get_current(self) -> dict:
        """Fetch current weather conditions.

        Returns dict with keys: temp_c, condition, humidity, wind_kph, location_name.
        Raises RuntimeError on API failure.
        """
        resp = requests.get(
            f"{WEATHER_API_URL}/current.json",
            params={"key": self._api_key, "q": self.location},
            timeout=10,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Weather API error: {resp.status_code} — {resp.text}")

        data = resp.json()
        current = data["current"]
        return {
            "temp_c": current["temp_c"],
            "condition": current["condition"]["text"],
            "humidity": current["humidity"],
            "wind_kph": current["wind_kph"],
            "location_name": data["location"]["name"],
        }

    def get_forecast(self) -> dict:
        """Fetch today's forecast with rain probability.

        Returns dict with keys: max_temp_c, min_temp_c, chance_of_rain, condition, location_name.
        Raises RuntimeError on API failure.
        """
        resp = requests.get(
            f"{WEATHER_API_URL}/forecast.json",
            params={"key": self._api_key, "q": self.location, "days": 1},
            timeout=10,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Weather API error: {resp.status_code} — {resp.text}")

        data = resp.json()
        day = data["forecast"]["forecastday"][0]["day"]
        return {
            "max_temp_c": day["maxtemp_c"],
            "min_temp_c": day["mintemp_c"],
            "chance_of_rain": day["daily_chance_of_rain"],
            "condition": day["condition"]["text"],
            "location_name": data["location"]["name"],
        }

    def get_summary(self) -> str:
        """Get a natural-language weather summary suitable for voice output."""
        try:
            current = self.get_current()
            forecast = self.get_forecast()
        except RuntimeError as e:
            return f"Sorry, I couldn't fetch the weather right now. {e}"
        except requests.ConnectionError:
            return "Sorry, I can't reach the weather service right now."

        summary = (
            f"It's currently {current['temp_c']:.0f} degrees and {current['condition'].lower()} "
            f"in {current['location_name']}. "
            f"Today's high is {forecast['max_temp_c']:.0f} and the low is {forecast['min_temp_c']:.0f} degrees."
        )

        rain_chance = int(forecast["chance_of_rain"])
        if rain_chance >= 50:
            summary += f" There's a {rain_chance}% chance of rain, so you might want to take an umbrella."

        return summary
