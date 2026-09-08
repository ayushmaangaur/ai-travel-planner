from models.trip import TravelRequest, DayPlan, Activity
from services.llm_service import LLMService


class ItineraryGenerator:
    """
    Generates a destination-aware itinerary using Gemini.

    Gemini is responsible for:
    - destination-specific attractions
    - activity descriptions
    - locations
    - durations
    - estimated activity costs
    - meals
    - travel tips
    - weather notes

    Python is responsible for:
    - converting the response into DayPlan objects
    - handling flight arrival timing
    - adding arrival/check-in activity
    - adding departure preparation
    """

    def __init__(self, llm_service=None):
        self.llm_service = llm_service or LLMService()

    def generate(
        self,
        request: TravelRequest,
        flight_recommendation=None,
        hotel_recommendation=None,
        weather_recommendation=None,
    ) -> list[DayPlan]:

        itinerary = self.llm_service.generate_itinerary(
            request=request,
            flight_recommendation=flight_recommendation,
            hotel_recommendation=hotel_recommendation,
            weather_recommendation=weather_recommendation,
        )

        if not itinerary:
            return []

        self._apply_hotel_information(
            itinerary,
            hotel_recommendation,
        )

        self._apply_weather_information(
            itinerary,
            weather_recommendation,
        )

        self._apply_arrival_information(
            itinerary,
            flight_recommendation,
        )

        self._apply_departure_information(
            itinerary,
        )

        return itinerary

    # ================================================================
    # HOTEL
    # ================================================================

    def _apply_hotel_information(
        self,
        itinerary: list[DayPlan],
        hotel_recommendation,
    ):
        """
        Add the selected/first hotel as a practical Day 1 tip.

        Hotel pricing is handled separately by BudgetEngine.
        """

        if not itinerary or hotel_recommendation is None:
            return

        options = getattr(
            hotel_recommendation,
            "options",
            [],
        )

        if not options:
            return

        hotel = options[0]

        hotel_name = getattr(
            hotel,
            "name",
            None,
        )

        hotel_location = getattr(
            hotel,
            "location",
            None,
        )

        if not hotel_name:
            return

        tip = f"Stay at {hotel_name}"

        if hotel_location:
            tip += f" in {hotel_location}"

        tip += "."

        if tip not in itinerary[0].travel_tips:
            itinerary[0].travel_tips.insert(
                0,
                tip,
            )

        # If Day 1 has activities without locations, don't overwrite
        # the LLM-generated location information.
        #
        # The hotel information is therefore primarily exposed through
        # the travel tip.

    # ================================================================
    # WEATHER
    # ================================================================

    def _apply_weather_information(
        self,
        itinerary: list[DayPlan],
        weather_recommendation,
    ):
        """
        Add deterministic weather notes from WeatherAgent output.

        This prevents weather information from being lost even if the
        LLM does not explicitly include it in its generated JSON.
        """

        if not itinerary or weather_recommendation is None:
            return

        forecast = getattr(
            weather_recommendation,
            "forecast",
            [],
        )

        if not forecast:
            return

        for index, weather_day in enumerate(forecast):

            if index >= len(itinerary):
                break

            condition = getattr(
                weather_day,
                "condition",
                None,
            )

            temperature = getattr(
                weather_day,
                "temperature",
                None,
            )

            precipitation = getattr(
                weather_day,
                "precipitation",
                None,
            )

            parts = []

            if condition:
                parts.append(str(condition))

            if temperature:
                parts.append(str(temperature))

            if precipitation:
                parts.append(
                    f"precipitation {precipitation}"
                )

            if not parts:
                continue

            note = "Weather: " + ", ".join(parts) + "."

            itinerary[index].weather_note = note

    # ================================================================
    # ARRIVAL
    # ================================================================

    def _apply_arrival_information(
        self,
        itinerary: list[DayPlan],
        flight_recommendation,
    ):
        """
        Add arrival/check-in to Day 1 based on the flight arrival time.

        Before 14:00 -> morning
        14:00-17:59 -> afternoon
        18:00+ -> evening
        """

        if not itinerary:
            return

        arrival_time = None

        if flight_recommendation is not None:

            options = getattr(
                flight_recommendation,
                "options",
                [],
            )

            if options:
                arrival_time = getattr(
                    options[0],
                    "arrival_time",
                    None,
                )

        arrival_activity = Activity(
            name="Arrival and check-in",
            description=(
                "Arrive at the destination, transfer to the hotel "
                "and settle in."
            ),
            location=None,
            duration="1-2 hours",
            estimated_cost=0.0,
            currency="INR",
        )

        period = self._get_arrival_period(
            arrival_time
        )

        day_one = itinerary[0]

        # Avoid duplicate arrival activities if Gemini happened
        # to generate one itself.
        self._remove_existing_arrival_activity(
            day_one
        )

        if period == "morning":
            day_one.morning.insert(
                0,
                arrival_activity,
            )

        elif period == "afternoon":
            day_one.afternoon.insert(
                0,
                arrival_activity,
            )

        else:
            day_one.evening.insert(
                0,
                arrival_activity,
            )

    @staticmethod
    def _get_arrival_period(
        arrival_time: str | None,
    ) -> str:

        if not arrival_time:
            return "morning"

        try:
            hour, minute = map(
                int,
                arrival_time.split(":")[:2],
            )
        except (
            ValueError,
            AttributeError,
        ):
            return "morning"

        total_minutes = (
            hour * 60
            + minute
        )

        if total_minutes >= 18 * 60:
            return "evening"

        if total_minutes >= 14 * 60:
            return "afternoon"

        return "morning"

    @staticmethod
    def _remove_existing_arrival_activity(
        day: DayPlan,
    ):
        """
        Remove an arrival/check-in activity generated by the LLM
        so that Python owns this deterministic behavior.
        """

        arrival_names = {
            "arrival and check-in",
            "arrival and hotel check-in",
            "arrival",
            "hotel check-in",
        }

        for activities in (
            day.morning,
            day.afternoon,
            day.evening,
        ):
            activities[:] = [
                activity
                for activity in activities
                if activity.name.lower().strip()
                not in arrival_names
            ]

    # ================================================================
    # DEPARTURE
    # ================================================================

    def _apply_departure_information(
        self,
        itinerary: list[DayPlan],
    ):
        """
        Add departure preparation to the final day.

        This is deterministic because it is a structural requirement
        of the itinerary rather than a destination recommendation.
        """

        if not itinerary:
            return

        final_day = itinerary[-1]

        departure_names = {
            "departure preparation",
            "departure",
            "check-out and departure",
        }

        for activities in (
            final_day.morning,
            final_day.afternoon,
            final_day.evening,
        ):
            if any(
                activity.name.lower().strip()
                in departure_names
                for activity in activities
            ):
                return

        departure_activity = Activity(
            name="Departure Preparation",
            description=(
                "Check out of the hotel, collect your belongings "
                "and prepare for departure."
            ),
            location=None,
            duration="1-2 hours",
            estimated_cost=0.0,
            currency="INR",
        )

        final_day.evening.append(
            departure_activity
        )