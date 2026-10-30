
import pytest
import requests

from services.weather_service import WeatherService


class FakeResponse:
    """Simulates an HTTP response without calling a real API."""

    def __init__(self, payload, error=None):
        self.payload = payload
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.payload


class FakeHTTP:
    """Records HTTP requests and returns a predefined response."""

    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self.response


def test_get_coordinates_returns_location():
    http = FakeHTTP(
        FakeResponse({
            "results": [
                {
                    "name": "Goa",
                    "latitude": 15.2993,
                    "longitude": 74.1240,
                    "timezone": "Asia/Kolkata",
                }
            ]
        })
    )

    service = WeatherService(http=http)

    result = service.get_coordinates("Goa")

    assert result["name"] == "Goa"
    assert result["latitude"] == 15.2993
    assert result["longitude"] == 74.1240
    assert result["timezone"] == "Asia/Kolkata"

    # Verify that the correct endpoint was called.
    assert http.calls[0]["url"] == service.GEOCODING_URL
    assert http.calls[0]["params"]["name"] == "Goa"
    assert http.calls[0]["timeout"] == 10


def test_get_coordinates_raises_for_unknown_destination():
    http = FakeHTTP(FakeResponse({"results": []}))
    service = WeatherService(http=http)

    with pytest.raises(ValueError, match="Could not find a location"):
        service.get_coordinates("UnknownPlace123")

 
def test_get_coordinates_propagates_http_error():
    http = FakeHTTP(
        FakeResponse(
            {},
            error=requests.HTTPError("API unavailable"),
        )
    )
    service = WeatherService(http=http)

    with pytest.raises(requests.HTTPError, match="API unavailable"):
        service.get_coordinates("Goa")


def test_get_forecast_uses_forecast_days():
    http = FakeHTTP(
        FakeResponse({
            "daily": {
                "time": ["2026-10-30"],
                "weather_code": [0],
                "temperature_2m_max": [32],
                "temperature_2m_min": [25],
                "precipitation_probability_max": [10],
            }
        })
    )
    service = WeatherService(http=http)

    result = service.get_forecast(
        latitude=15.2993,
        longitude=74.1240,
        days=1,
        timezone="Asia/Kolkata",
    )

    assert "daily" in result

    call = http.calls[0]
    assert call["url"] == service.FORECAST_URL
    assert call["params"]["forecast_days"] == 1
    assert call["params"]["timezone"] == "Asia/Kolkata"
    assert call["params"]["temperature_unit"] == "celsius"


def test_get_forecast_uses_requested_date_range():
    http = FakeHTTP(FakeResponse({"daily": {}}))
    service = WeatherService(http=http)

    service.get_forecast(
        latitude=15.2993,
        longitude=74.1240,
        days=3,
        start_date="2026-11-01",
    )

    params = http.calls[0]["params"]

    assert params["start_date"] == "2026-11-01"
    assert params["end_date"] == "2026-11-03"
    assert "forecast_days" not in params


@pytest.mark.parametrize("days", [0, -1, 17])
def test_get_forecast_rejects_invalid_duration(days):
    http = FakeHTTP(FakeResponse({}))
    service = WeatherService(http=http)

    with pytest.raises(ValueError, match="between 1 and 16 days"):
        service.get_forecast(
            latitude=15.2993,
            longitude=74.1240,
            days=days,
        )

    # Invalid requests must be rejected before making an HTTP call.
    assert http.calls == []


def test_get_forecast_rejects_invalid_date():
    http = FakeHTTP(FakeResponse({}))
    service = WeatherService(http=http)

    with pytest.raises(ValueError):
        service.get_forecast(
            latitude=15.2993,
            longitude=74.1240,
            days=3,
            start_date="not-a-date",
        )

    assert http.calls == []


def test_get_forecast_rejects_missing_daily_data():
    http = FakeHTTP(FakeResponse({"error": "Invalid request"}))
    service = WeatherService(http=http)

    with pytest.raises(
        ValueError,
        match="did not contain daily forecasts",
    ):
        service.get_forecast(
            latitude=15.2993,
            longitude=74.1240,
            days=1,
        )


def test_describe_weather_code():
    assert service_description(0) == "Clear sky"
    assert service_description(95) == "Thunderstorm"
    assert service_description(999) == "Unknown conditions"


def service_description(code):
    return WeatherService.describe_weather_code(code)


def test_get_coordinates_propagates_connection_error():
    class ConnectionFailureHTTP:
        def get(self, url, **kwargs):
            raise requests.ConnectionError("Network unavailable")

    service = WeatherService(http=ConnectionFailureHTTP())

    with pytest.raises(requests.ConnectionError, match="Network unavailable"):
        service.get_coordinates("Goa")


def test_get_coordinates_handles_invalid_json():
    class InvalidJSONResponse(FakeResponse):
        def json(self):
            raise ValueError("Invalid JSON")

    service = WeatherService(http=FakeHTTP(InvalidJSONResponse({})))

    with pytest.raises(ValueError, match="Invalid JSON"):
        service.get_coordinates("Goa")


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        "invalid response",
        {"results": "not a list"},
        {"results": [None]},
        {"results": [{"name": "Goa"}]},
        {"results": [{"name": "Goa", "latitude": "invalid",
                      "longitude": 74.1240}]},
        {"results": [{"name": "Goa", "latitude": 15.2993,
                      "longitude": 200}]},
    ],
)
def test_get_coordinates_rejects_malformed_response(payload):
    service = WeatherService(http=FakeHTTP(FakeResponse(payload)))

    with pytest.raises(ValueError):
        service.get_coordinates("Goa")


def test_get_forecast_propagates_timeout():
    class TimeoutHTTP:
        def get(self, url, **kwargs):
            raise requests.Timeout("Request timed out")

    service = WeatherService(http=TimeoutHTTP())

    with pytest.raises(requests.Timeout, match="Request timed out"):
        service.get_forecast(
            latitude=15.2993,
            longitude=74.1240,
            days=1,
        )


def test_get_forecast_handles_invalid_json():
    class InvalidJSONResponse(FakeResponse):
        def json(self):
            raise ValueError("Invalid JSON")

    service = WeatherService(http=FakeHTTP(InvalidJSONResponse({})))

    with pytest.raises(ValueError, match="Invalid JSON"):
        service.get_forecast(
            latitude=15.2993,
            longitude=74.1240,
            days=1,
        )


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        "invalid response",
        {"daily": None},
        {"daily": []},
        {"error": "Invalid request"},
    ],
)
def test_get_forecast_rejects_malformed_response(payload):
    service = WeatherService(http=FakeHTTP(FakeResponse(payload)))

    with pytest.raises(ValueError):
        service.get_forecast(
            latitude=15.2993,
            longitude=74.1240,
            days=1,
        )


def test_get_forecast_rejects_invalid_coordinates():
    service = WeatherService(http=FakeHTTP(FakeResponse({})))

    with pytest.raises(ValueError, match="latitude"):
        service.get_forecast(
            latitude=100,
            longitude=74.1240,
            days=1,
        )

    assert service.http.calls == []


def test_get_forecast_rejects_invalid_longitude():
    service = WeatherService(http=FakeHTTP(FakeResponse({})))

    with pytest.raises(ValueError, match="longitude"):
        service.get_forecast(
            latitude=15.2993,
            longitude=200,
            days=1,
        )

    assert service.http.calls == []
