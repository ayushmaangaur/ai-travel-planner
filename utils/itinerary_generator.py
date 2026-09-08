from models.trip import TravelRequest, DayPlan, Activity
from services.activity_cost_estimator import ActivityCostEstimator

class ItineraryGenerator:

    def __init__(self):
        self.cost_estimator = ActivityCostEstimator()

    def _activity_cost(self, name: str) -> float:
        return self.cost_estimator.estimate(name)

    def _get_arrival_period(self, arrival_time: str | None) -> str:
        if not arrival_time:
            return "morning"

        try:
            hour, minute = map(
                int,
                arrival_time.split(":")[:2]
            )
        except (ValueError, AttributeError):
            return "morning"

        total_minutes = hour * 60 + minute

        if total_minutes >= 18 * 60:
            return "evening"

        if total_minutes >= 14 * 60:
            return "afternoon"

        return "morning"

    def generate(
        self,
        request: TravelRequest,
        flight_result,
        hotel_result,
        weather_result,
    ) -> list[DayPlan]:

        days = request.days or 0

        if days <= 0:
            return []

        itinerary = []

        # ========================================================
        # EXTRACT HOTEL INFORMATION
        # ========================================================

        hotel_name = None
        hotel_location = None

        if hotel_result and getattr(hotel_result, "options", None):
            hotel = hotel_result.options[0]

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

        # ========================================================
        # EXTRACT FLIGHT INFORMATION
        # ========================================================

        arrival_time = None

        if flight_result and getattr(
            flight_result,
            "options",
            None,
        ):
            flight = flight_result.options[0]

            arrival_time = getattr(
                flight,
                "arrival_time",
                None,
            )

        # ========================================================
        # EXTRACT WEATHER INFORMATION
        # ========================================================

        forecast = []

        if weather_result:
            forecast = getattr(
                weather_result,
                "forecast",
                [],
            )

            if not isinstance(forecast, list):
                forecast = []

        # ========================================================
        # GENERATE ITINERARY
        # ========================================================

        for day in range(1, days + 1):

            # ----------------------------------------------------
            # WEATHER
            # ----------------------------------------------------

            weather_note = None

            if day <= len(forecast):

                weather = forecast[day - 1]

                condition = getattr(
                    weather,
                    "condition",
                    None,
                )

                temperature = getattr(
                    weather,
                    "temperature",
                    None,
                )

                precipitation = getattr(
                    weather,
                    "precipitation",
                    None,
                )

                weather_parts = []

                if condition:
                    weather_parts.append(
                        str(condition)
                    )

                if temperature:
                    weather_parts.append(
                        str(temperature)
                    )

                if precipitation:
                    weather_parts.append(
                        f"precipitation {precipitation}"
                    )

                if weather_parts:
                    weather_note = ", ".join(
                        weather_parts
                    )

            # ====================================================
            # DAY 1
            # ====================================================

            if day == 1:

                arrival_period = self._get_arrival_period(
                    arrival_time
                )

                arrival_description = (
                    "Arrive and settle into the destination."
                )

                if arrival_time:
                    arrival_description = (
                        f"Arrive around {arrival_time}, "
                        "settle in, and begin exploring."
                    )

                arrival_activity = Activity(
                    name="Arrival and check-in",
                    description=arrival_description,
                    location=hotel_location,
                    duration="2 hours",
                    estimated_cost=self._activity_cost(
                        "Arrival and check-in"
                    ),
                    currency="INR",
                )

                nearby_activity = Activity(
                    name="Explore nearby area",
                    description=(
                        f"Explore the nearby area of "
                        f"{request.destination}."
                    ),
                    location=hotel_location,
                    duration="2-3 hours",
                    estimated_cost=self._activity_cost(
                        "Explore nearby area"
                    ),
                    currency="INR",
                )

                dinner_activity = Activity(
                    name="Local dinner",
                    description=(
                        "Enjoy a relaxed dinner "
                        "and experience local cuisine."
                    ),
                    location=request.destination,
                    duration="1-2 hours",
                    estimated_cost=self._activity_cost(
                        "Local dinner"
                    ),
                    currency="INR",
                )

                morning = []
                afternoon = []
                evening = []

                if arrival_period == "morning":
                    morning.append(arrival_activity)
                    afternoon.append(nearby_activity)
                    evening.append(dinner_activity)

                elif arrival_period == "afternoon":
                    afternoon.append(arrival_activity)
                    evening.extend([
                        nearby_activity,
                        dinner_activity,
                    ])

                else:
                    evening.extend([
                        arrival_activity,
                        dinner_activity,
                    ])

                travel_tips = []

                if hotel_name:
                    travel_tips.append(
                        f"Check in to {hotel_name}."
                    )

                travel_tips.append(
                    "Keep the first day relaxed after travelling."
                )

                itinerary.append(
                    DayPlan(
                        day=day,
                        title="Arrival and Exploration",
                        summary=(
                            f"Arrive in {request.destination}, "
                            "settle in, and explore the nearby area."
                        ),
                        morning=morning,
                        afternoon=afternoon,
                        evening=evening,
                        meals=[
                            "Lunch",
                            "Dinner",
                        ],
                        travel_tips=travel_tips,
                        weather_note=weather_note,
                    )
                )

            # ====================================================
            # FINAL DAY
            # ====================================================

            elif day == days:

                morning = [
                    Activity(
                        name="Morning sightseeing",
                        description=(
                            f"Enjoy a relaxed morning "
                            f"in {request.destination}."
                        ),
                        location=request.destination,
                        duration="2-3 hours",
                        estimated_cost=self._activity_cost(
                            "Morning sightseeing"
                        ),
                        currency="INR",
                    )
                ]

                afternoon = [
                    Activity(
                        name="Shopping and local exploration",
                        description=(
                            "Do some shopping or explore "
                            "local markets before departure."
                        ),
                        location=request.destination,
                        duration="2-3 hours",
                        estimated_cost=self._activity_cost(
                            "Shopping and local exploration"
                        ),
                        currency="INR",
                    )
                ]

                evening = [
                    Activity(
                        name="Departure preparation",
                        description=(
                            "Prepare for departure and "
                            "complete the final check-out."
                        ),
                        location=hotel_location,
                        duration="1 hour",
                        estimated_cost=self._activity_cost(
                            "Departure preparation"
                        ),
                        currency="INR",
                    )
                ]

                itinerary.append(
                    DayPlan(
                        day=day,
                        title="Final Day",
                        summary=(
                            f"Enjoy a relaxed final day in "
                            f"{request.destination} before departure."
                        ),
                        morning=morning,
                        afternoon=afternoon,
                        evening=evening,
                        meals=[
                            "Breakfast",
                            "Lunch",
                        ],
                        travel_tips=[
                            "Keep enough time for checkout and departure."
                        ],
                        weather_note=weather_note,
                    )
                )

            # ====================================================
            # NORMAL DAYS
            # ====================================================

            else:

                morning = [
                    Activity(
                        name="Explore major attractions",
                        description=(
                            f"Explore major attractions "
                            f"and landmarks in "
                            f"{request.destination}."
                        ),
                        location=request.destination,
                        duration="3 hours",
                        estimated_cost=self._activity_cost(
                            "Explore major attractions"
                        ),
                        currency="INR",
                    )
                ]

                afternoon = [
                    Activity(
                        name="Local experience",
                        description=(
                            "Experience local culture, "
                            "food, and attractions."
                        ),
                        location=request.destination,
                        duration="3 hours",
                        estimated_cost=self._activity_cost(
                            "Local experience"
                        ),
                        currency="INR",
                    )
                ]

                evening = [
                    Activity(
                        name="Evening exploration",
                        description=(
                            "Enjoy the evening and "
                            "explore local food options."
                        ),
                        location=request.destination,
                        duration="2 hours",
                        estimated_cost=self._activity_cost(
                            "Evening exploration"
                        ),
                        currency="INR",
                    )
                ]

                itinerary.append(
                    DayPlan(
                        day=day,
                        title=f"Explore {request.destination}",
                        summary=(
                            f"Explore major attractions and "
                            f"local experiences in "
                            f"{request.destination}."
                        ),
                        morning=morning,
                        afternoon=afternoon,
                        evening=evening,
                        meals=[
                            "Breakfast",
                            "Lunch",
                            "Dinner",
                        ],
                        travel_tips=[
                            "Use local transportation "
                            "to move between attractions."
                        ],
                        weather_note=weather_note,
                    )
                )

        return itinerary