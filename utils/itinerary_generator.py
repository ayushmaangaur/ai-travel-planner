from models.trip import TravelRequest


class ItineraryGenerator:

    def generate(
        self,
        request: TravelRequest,
        flight_result,
        hotel_result,
        weather_result
    ) -> list[str]:

        days = request.days or 0

        if days <= 0:
            return []

        itinerary = []

        # -----------------------------
        # Extract hotel information
        # -----------------------------

        hotel_name = None
        hotel_location = None

        if hotel_result and getattr(hotel_result, "options", None):
            hotel = hotel_result.options[0]
            hotel_name = getattr(hotel, "name", None)
            hotel_location = getattr(hotel, "location", None)

        # -----------------------------
        # Extract flight information
        # -----------------------------

        arrival_time = None

        if flight_result and getattr(flight_result, "options", None):
            flight = flight_result.options[0]
            arrival_time = getattr(flight, "arrival_time", None)

        # -----------------------------
        # Extract weather information
        # -----------------------------

        forecast = []

        if weather_result:
            forecast = getattr(weather_result, "forecast", [])

            if not isinstance(forecast, list):
                forecast = []

        # -----------------------------
        # Generate itinerary
        # -----------------------------

        for day in range(1, days + 1):

            weather_text = ""

            if day <= len(forecast):
                weather = forecast[day - 1]

                condition = getattr(weather, "condition", None)
                temperature = getattr(weather, "temperature", None)
                precipitation = getattr(weather, "precipitation", None)

                weather_parts = []

                if condition:
                    weather_parts.append(str(condition))

                if temperature:
                    weather_parts.append(str(temperature))

                if precipitation:
                    weather_parts.append(
                        f"precipitation {precipitation}"
                    )

                if weather_parts:
                    weather_text = (
                        " Weather: "
                        + ", ".join(weather_parts)
                        + "."
                    )

            # -------------------------
            # Day 1
            # -------------------------

            if day == 1:

                arrival_text = ""

                if arrival_time:
                    arrival_text = (
                        f" Arrive around {arrival_time} and "
                    )

                hotel_text = ""

                if hotel_name:
                    hotel_text = (
                        f" Check in to {hotel_name}"
                    )

                    if hotel_location:
                        hotel_text += f" in {hotel_location}"

                    hotel_text += "."

                itinerary.append(
                    f"Day 1: {arrival_text}"
                    f"settle in and explore the nearby area."
                    f"{hotel_text}"
                    f"{weather_text}"
                )

            # -------------------------
            # Final day
            # -------------------------

            elif day == days:

                itinerary.append(
                    f"Day {day}: Enjoy a relaxed final day in "
                    f"{request.destination}, do some shopping or "
                    f"sightseeing, and prepare for departure."
                    f"{weather_text}"
                )

            # -------------------------
            # Normal days
            # -------------------------

            else:

                itinerary.append(
                    f"Day {day}: Explore major attractions and "
                    f"local experiences in {request.destination}. "
                    f"Enjoy local food and take breaks throughout "
                    f"the day."
                    f"{weather_text}"
                )

        return itinerary