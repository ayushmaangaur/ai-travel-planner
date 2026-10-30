
from models.trip import TravelRequest
from models.weather import WeatherDay, WeatherRecommendation
from services.weather_service import WeatherService


class WeatherAgent:
    REQUIRED_DAILY_FIELDS = (
        "time",
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_probability_max",
    )

    def __init__(self, weather_service=None):
        # Dependency injection keeps the agent easy to test.
        self.weather_service = (
            weather_service
            if weather_service is not None
            else WeatherService()
        )

    def get_weather(
        self,
        request: TravelRequest,
    ) -> WeatherRecommendation:
        if not request.destination:
            raise ValueError("A destination is required for weather.")

        if not isinstance(request.days, int) or isinstance(request.days, bool):
            raise ValueError("Trip duration must be a whole number of days.")

        if not 1 <= request.days <= 16:
            raise ValueError("Trip duration must be between 1 and 16 days.")

        # Step 1: Resolve the destination.
        location = self.weather_service.get_coordinates(
            request.destination
        )

        if not isinstance(location, dict):
            raise ValueError("Weather location response must be an object.")

        for field in ("name", "latitude", "longitude"):
            if field not in location or location[field] is None:
                raise ValueError(
                    f"Weather location response is missing '{field}'."
                )

        timezone = location.get("timezone") or "auto"

        # Step 2: Fetch the forecast.
        data = self.weather_service.get_forecast(
            latitude=location["latitude"],
            longitude=location["longitude"],
            days=request.days,
            start_date=request.start_date,
            timezone=timezone,
        )

        daily = self._validate_daily_data(data)

        dates = daily["time"]
        codes = daily["weather_code"]
        max_temps = daily["temperature_2m_max"]
        min_temps = daily["temperature_2m_min"]
        rain_chances = daily["precipitation_probability_max"]

        forecast = []

        for index, forecast_date in enumerate(dates):
            code = codes[index]
            max_temp = max_temps[index]
            min_temp = min_temps[index]
            rain_chance = rain_chances[index]

            condition = (
                self.weather_service.describe_weather_code(code)
                if code is not None
                else "Unknown conditions"
            )

            if max_temp is None or min_temp is None:
                temperature = "Temperature unavailable"
            else:
                temperature = (
                    f"High {max_temp}°C / Low {min_temp}°C"
                )

            precipitation = (
                f"Up to {rain_chance}% chance of precipitation"
                if rain_chance is not None
                else "Precipitation probability unavailable"
            )

            forecast.append(
                WeatherDay(
                    date=forecast_date,
                    condition=condition,
                    temperature=temperature,
                    precipitation=precipitation,
                )
            )

        return WeatherRecommendation(
            destination=location["name"],
            forecast=forecast,
        )

    @classmethod
    def _validate_daily_data(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Weather API response must be an object.")

        daily = data.get("daily")

        if not isinstance(daily, dict):
            raise ValueError(
                "Weather API response must contain a valid 'daily' object."
            )

        for field in cls.REQUIRED_DAILY_FIELDS:
            if field not in daily:
                raise ValueError(
                    f"Weather API daily response is missing '{field}'."
                )

            if not isinstance(daily[field], list):
                raise ValueError(
                    f"Weather API field '{field}' must be a list."
                )

        expected_length = len(daily["time"])

        for field in cls.REQUIRED_DAILY_FIELDS:
            if len(daily[field]) != expected_length:
                raise ValueError(
                    "Weather API daily arrays must contain the "
                    "same number of entries."
                )

        for index, forecast_date in enumerate(daily["time"]):
            if not isinstance(forecast_date, str) or not forecast_date:
                raise ValueError(
                    f"Weather API returned an invalid date at index {index}."
                )

        return daily
