from dataclasses import dataclass


@dataclass
class WeatherDay:
    date: str
    condition: str
    temperature: str
    precipitation: str


@dataclass
class WeatherRecommendation:
    destination: str
    forecast: list[WeatherDay]