
from datetime import date, timedelta
import math

import requests


class WeatherService:
    GEOCODING_URL = (
        "https://geocoding-api.open-meteo.com/v1/search"
    )
    FORECAST_URL = (
        "https://api.open-meteo.com/v1/forecast"
    )
    REQUEST_TIMEOUT = 10

    def __init__(self, http=requests):
        # Dependency injection lets tests use fake HTTP clients.
        self.http = http

    @staticmethod
    def _is_valid_number(value):
        """Return True for finite numeric values, excluding booleans."""
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )

    def get_coordinates(self, destination: str) -> dict:
        """Resolve a destination name into geographic coordinates."""

        if not isinstance(destination, str) or not destination.strip():
            raise ValueError("Destination must be a non-empty string.")

        response = self.http.get(
            self.GEOCODING_URL,
            params={
                "name": destination.strip(),
                "count": 10,
                "language": "en",
                "format": "json",
            },
            timeout=self.REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise ValueError(
                "Geocoding API response must be an object."
            )

        results = data.get("results", [])

        if not isinstance(results, list):
            raise ValueError(
                "Geocoding API 'results' field must be a list."
            )

        if not results:
            raise ValueError(
                f"Could not find a location for '{destination}'."
            )

        # Initially choose the first geocoding match.
        place = results[0]

        if not isinstance(place, dict):
            raise ValueError(
                "Geocoding API returned an invalid location."
            )

        name = place.get("name")
        latitude = place.get("latitude")
        longitude = place.get("longitude")

        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "Geocoding API location is missing a valid name."
            )

        if not self._is_valid_number(latitude):
            raise ValueError(
                "Geocoding API returned an invalid latitude."
            )

        if not -90 <= latitude <= 90:
            raise ValueError(
                "Geocoding API latitude must be between -90 and 90."
            )

        if not self._is_valid_number(longitude):
            raise ValueError(
                "Geocoding API returned an invalid longitude."
            )

        if not -180 <= longitude <= 180:
            raise ValueError(
                "Geocoding API longitude must be between -180 and 180."
            )

        timezone = place.get("timezone") or "auto"

        if not isinstance(timezone, str):
            raise ValueError(
                "Geocoding API returned an invalid timezone."
            )

        return {
            "name": name.strip(),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
        }

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int,
        start_date: str | None = None,
        timezone: str = "auto",
    ) -> dict:
        """Fetch daily forecast data for the requested trip."""

        if not self._is_valid_number(latitude):
            raise ValueError("Latitude must be a valid number.")

        if not -90 <= latitude <= 90:
            raise ValueError("Invalid latitude: must be between -90 and 90.")

        if not self._is_valid_number(longitude):
            raise ValueError("Longitude must be a valid number.")

        if not -180 <= longitude <= 180:
            raise ValueError(
                "Invalid longitude: must be between -180 and 180."
            )

        if (
            not isinstance(days, int)
            or isinstance(days, bool)
            or not 1 <= days <= 16
        ):
            raise ValueError(
                "Forecast duration must be between 1 and 16 days."
            )

        if not isinstance(timezone, str) or not timezone.strip():
            raise ValueError("Timezone must be a non-empty string.")

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": (
                "weather_code,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max"
            ),
            "temperature_unit": "celsius",
            "timezone": timezone,
        }

        if start_date is not None:
            if not isinstance(start_date, str):
                raise ValueError(
                    "Start date must be a valid YYYY-MM-DD date."
                )

            try:
                trip_start = date.fromisoformat(start_date)
            except ValueError as exc:
                raise ValueError(
                    "Start date must be a valid YYYY-MM-DD date."
                ) from exc

            # Require the canonical ISO date format.
            if trip_start.isoformat() != start_date:
                raise ValueError(
                    "Start date must use the YYYY-MM-DD format."
                )

            trip_end = trip_start + timedelta(days=days - 1)

            params["start_date"] = trip_start.isoformat()
            params["end_date"] = trip_end.isoformat()
        else:
            params["forecast_days"] = days

        response = self.http.get(
            self.FORECAST_URL,
            params=params,
            timeout=self.REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise ValueError(
                "Weather API response must be an object."
            )

        if "daily" not in data:
            raise ValueError(
                "Weather API response did not contain daily forecasts."
            )

        if not isinstance(data["daily"], dict):
            raise ValueError(
                "Weather API daily forecasts must be an object."
            )

        return data

    @staticmethod
    def describe_weather_code(code: int) -> str:
        """Convert a WMO weather code into a readable description."""

        descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snowfall",
            73: "Moderate snowfall",
            75: "Heavy snowfall",
            80: "Rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with hail",
            99: "Thunderstorm with heavy hail",
        }

        return descriptions.get(code, "Unknown conditions")
