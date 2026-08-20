import re

from services.llm_service import LLMService
from prompts.system_prompts import ROOT_AGENT_PROMPT
from utils.validator import TravelRequestValidator
from models.session import ConversationSession
from models.trip import TravelPlan, TravelRequest

from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.weather_agent import WeatherAgent
from utils.itinerary_generator import ItineraryGenerator


class RootTravelAgent:

    def __init__(self):
        self.llm = LLMService()
        self.system_prompt = ROOT_AGENT_PROMPT
        self.session = ConversationSession()

        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.weather_agent = WeatherAgent()

        self.itinerary_generator = ItineraryGenerator()


    def extract_local_fields(self, user_message: str) -> TravelRequest:
        """
        Extract structured travel information directly from the user's
        message without making a Gemini API call.

        This handles common natural-language patterns for:
        - current location
        - origin
        - destination
        - days
        - travelers
        - budget
        - flight/travel preference
        """

        request = TravelRequest()

        text = user_message.strip()

        if not text:
            return request

        # ---------------------------------------------------------
        # DAYS
        # ---------------------------------------------------------

        days_match = re.search(
            r"\b(\d+)\s*(?:day|days|night|nights)\b",
            text,
            re.IGNORECASE
        )

        if days_match:
            request.days = int(days_match.group(1))

        # ---------------------------------------------------------
        # TRAVELERS
        # ---------------------------------------------------------

        travelers_match = re.search(
            r"\b(\d+)\s*(?:people|person|travellers?|travelers?|"
            r"adults?|pax)\b",
            text,
            re.IGNORECASE
        )

        if travelers_match:
            request.travelers = int(travelers_match.group(1))

        # ---------------------------------------------------------
        # BUDGET
        # ---------------------------------------------------------

        budget_match = re.search(
            r"(?:budget|under|within|spend|cost)\s*(?:is|of|:)?\s*"
            r"(?:₹|rs\.?|inr)?\s*"
            r"([\d,]+(?:\.\d+)?)\s*"
            r"(?:rupees?|rs\.?|inr)?",
            text,
            re.IGNORECASE
        )

        if budget_match:
            budget_value = budget_match.group(1).replace(",", "")

            try:
                request.budget = float(budget_value)
            except ValueError:
                pass

        # Also support:
        # "60000 rupees"
        # "₹60000"
        # "60000 INR"
        if request.budget is None:

            standalone_budget_match = re.search(
                r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)"
                r"|"
                r"\b([\d,]+(?:\.\d+)?)\s*(?:rupees?|inr)\b",
                text,
                re.IGNORECASE
            )

            if standalone_budget_match:

                budget_value = (
                    standalone_budget_match.group(1)
                    or standalone_budget_match.group(2)
                )

                try:
                    request.budget = float(
                        budget_value.replace(",", "")
                    )
                except ValueError:
                    pass

        # ---------------------------------------------------------
        # CURRENT LOCATION / ORIGIN / DESTINATION
        # ---------------------------------------------------------

        # Pattern:
        # "I am in Delhi and want to travel to Tokyo"
        route_match = re.search(
            r"\b(?:i\s+am|i'm|im|currently\s+am|currently)\s+in\s+"
            r"([A-Za-z][A-Za-z .'-]*?)"
            r"\s+(?:and\s+)?(?:want|would like|plan|planning)"
            r"\s+to\s+(?:travel\s+)?to\s+"
            r"([A-Za-z][A-Za-z .'-]*?)"
            r"(?=\s+(?:for|with|on|under|within|and|"
            r"my|i\s+prefer|budget)\b|[.,!?]|$)",
            text,
            re.IGNORECASE
        )

        if route_match:

            current_location = route_match.group(1).strip()
            destination = route_match.group(2).strip()

            request.current_location = current_location
            request.origin = current_location
            request.destination = destination

        # ---------------------------------------------------------
        # "from Delhi to Tokyo"
        # ---------------------------------------------------------

        if request.destination is None:

            from_to_match = re.search(
                r"\bfrom\s+"
                r"([A-Za-z][A-Za-z .'-]*?)"
                r"\s+to\s+"
                r"([A-Za-z][A-Za-z .'-]*?)"
                r"(?=\s+(?:for|with|on|under|within|and|"
                r"my|i\s+prefer|budget)\b|[.,!?]|$)",
                text,
                re.IGNORECASE
            )

            if from_to_match:

                origin = from_to_match.group(1).strip()
                destination = from_to_match.group(2).strip()

                request.origin = origin
                request.destination = destination

        # ---------------------------------------------------------
        # "visit Tokyo from Delhi"
        # ---------------------------------------------------------

        if request.destination is None:

            visit_match = re.search(
                r"\b(?:visit|travel\s+to|go\s+to)\s+"
                r"([A-Za-z][A-Za-z .'-]*?)"
                r"(?:\s+from\s+([A-Za-z][A-Za-z .'-]*?))?"
                r"(?=\s+(?:for|with|on|under|within|and|"
                r"my|i\s+prefer|budget)\b|[.,!?]|$)",
                text,
                re.IGNORECASE
            )

            if visit_match:

                request.destination = visit_match.group(1).strip()

                if visit_match.group(2):
                    request.origin = visit_match.group(2).strip()

        # ---------------------------------------------------------
        # PREFERENCE
        # ---------------------------------------------------------

        preference_match = re.search(
            r"\b(?:i\s+)?prefer\s+"
            r"(.+?)"
            r"(?=\s*(?:[.!?]|$))",
            text,
            re.IGNORECASE
        )

        if preference_match:

            preference = preference_match.group(1).strip()

            if preference:
                request.preference = preference

        return request

    
    # ============================================================
    # PROMPT BUILDING
    # ============================================================

    def build_prompt(self, user_request: str) -> str:

        request = self.session.request

        return f"""
{self.system_prompt}

Current Travel Request:

Current Location: {request.current_location}
Origin: {request.origin}
Destination: {request.destination}
Days: {request.days}
Budget: {request.budget}
Travelers: {request.travelers}
Preference: {request.preference}

New User Message:

{user_request}
"""

    # ============================================================
    # MISSING INFORMATION
    # ============================================================

    def get_missing_fields(self) -> list[str]:
        """
        Determine which required travel fields are still missing.
        """

        return TravelRequestValidator.validate(
            self.session.request
        )

    def ask_for_missing_information(
        self,
        missing_fields: list[str]
    ) -> str:

        questions = {
            "current_location":
                "📍 Where are you currently located?",

            "origin":
                "✈️ Where would you like your journey to start from?",

            "destination":
                "🌍 Where would you like to travel?",

            "days":
                "📅 How many days are you planning to stay?",

            "budget":
                "💰 What's your approximate budget?",

            "travelers":
                "👥 How many people are travelling?",
        }

        return "\n".join(
            questions[field]
            for field in missing_fields
            if field in questions
        )

    # ============================================================
    # LOCAL FOLLOW-UP PARSER
    # ============================================================

    def parse_follow_up_locally(
        self,
        user_message: str,
        missing_fields: list[str]
    ) -> TravelRequest:

        """
        Parse follow-up answers WITHOUT calling Gemini.

        Examples:

        "50000"
        "50000 rupees"
        "2 people"
        "7 days"
        "Delhi"
        "Mumbai"
        "I prefer cheap flights"
        """

        text = user_message.strip()

        result = TravelRequest()

        # --------------------------------------------------------
        # Budget
        # --------------------------------------------------------

        if "budget" in missing_fields:

            budget_match = re.search(
                r"(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(?:rupees?|rs\.?|inr)?",
                text,
                re.IGNORECASE
            )

            if budget_match:
                try:
                    result.budget = float(
                        budget_match.group(1).replace(",", "")
                    )
                except ValueError:
                    pass

        # --------------------------------------------------------
        # Travelers
        # --------------------------------------------------------

        if "travelers" in missing_fields:

            traveler_match = re.search(
                r"(\d+)\s*(?:people|person|traveler|travelers|travelling|passengers?)",
                text,
                re.IGNORECASE
            )

            if traveler_match:
                result.travelers = int(
                    traveler_match.group(1)
                )

            # Also support just "2"
            elif text.isdigit():
                result.travelers = int(text)

        # --------------------------------------------------------
        # Days
        # --------------------------------------------------------

        if "days" in missing_fields:

            days_match = re.search(
                r"(\d+)\s*(?:days?|nights?)",
                text,
                re.IGNORECASE
            )

            if days_match:
                result.days = int(
                    days_match.group(1)
                )

        # --------------------------------------------------------
        # Preference
        # --------------------------------------------------------

        if "preference" in missing_fields:

            result.preference = text

        # --------------------------------------------------------
        # Current location / Origin
        # --------------------------------------------------------

        if "current_location" in missing_fields:

            location_match = re.search(
                r"(?:i am in|i'm in|currently in|from)\s+(.+)",
                text,
                re.IGNORECASE
            )

            if location_match:
                location = location_match.group(1).strip()

                # Remove trailing travel-related wording
                location = re.split(
                    r"\s+(?:and|but|with|for)\s+",
                    location,
                    maxsplit=1,
                    flags=re.IGNORECASE
                )[0]

                result.current_location = location

        if "origin" in missing_fields:

            origin_match = re.search(
                r"(?:from|origin is|starting from)\s+(.+)",
                text,
                re.IGNORECASE
            )

            if origin_match:
                origin = origin_match.group(1).strip()

                origin = re.split(
                    r"\s+(?:and|but|with|for)\s+",
                    origin,
                    maxsplit=1,
                    flags=re.IGNORECASE
                )[0]

                result.origin = origin

        # --------------------------------------------------------
        # Destination
        # --------------------------------------------------------

        if "destination" in missing_fields:

            destination_match = re.search(
                r"(?:visit|travel to|going to|go to|destination is)\s+(.+)",
                text,
                re.IGNORECASE
            )

            if destination_match:
                destination = destination_match.group(1).strip()

                destination = re.split(
                    r"\s+(?:and|but|with|for)\s+",
                    destination,
                    maxsplit=1,
                    flags=re.IGNORECASE
                )[0]

                result.destination = destination

        return result

    # ============================================================
    # DETERMINE ORIGIN
    # ============================================================

    def determine_origin(self):

        request = self.session.request

        if request.current_location and not request.origin:
            request.origin = request.current_location

    # ============================================================
    # PLAN TRIP
    # ============================================================

    def extract_request_locally(self, user_request: str) -> TravelRequest:
        """
        Extract common travel-request fields locally.

        This avoids Gemini calls for information that can be
        reliably extracted using simple patterns.
        """

        text = user_request.strip()

        extracted = TravelRequest()

        # ============================================================
        # DAYS
        # ============================================================

        days_match = re.search(
            r"\b(\d+)\s*(?:day|days)\b",
            text,
            re.IGNORECASE
        )

        if days_match:
            extracted.days = int(days_match.group(1))

        # ============================================================
        # TRAVELERS
        # ============================================================

        travelers_match = re.search(
            r"\b(\d+)\s*(?:people|person|travellers|travelers|pax)\b",
            text,
            re.IGNORECASE
        )

        if travelers_match:
            extracted.travelers = int(travelers_match.group(1))

        # Also support:
        # "for 2"
        # "for two people" is handled separately below if needed.
        if extracted.travelers is None:
            travelers_match = re.search(
                r"\bfor\s+(\d+)\b",
                text,
                re.IGNORECASE
            )

            if travelers_match:
                extracted.travelers = int(
                    travelers_match.group(1)
                )

        # ============================================================
        # BUDGET
        # ============================================================

        budget_match = re.search(
            r"(?:budget|under|within|costing|spend)\s*(?:is|of|:)?\s*"
            r"(?:₹|rs\.?|inr)?\s*([\d,]+)",
            text,
            re.IGNORECASE
        )

        if budget_match:
            budget_string = budget_match.group(1).replace(",", "")

            try:
                extracted.budget = float(budget_string)
            except ValueError:
                pass

        # Support:
        # "60000 rupees"
        # "60000 INR"
        if extracted.budget is None:

            budget_match = re.search(
                r"(?:₹|rs\.?|inr)?\s*([\d,]+)\s*"
                r"(?:rupees|rs|inr)",
                text,
                re.IGNORECASE
            )

            if budget_match:
                budget_string = budget_match.group(1).replace(",", "")

                try:
                    extracted.budget = float(budget_string)
                except ValueError:
                    pass

        # ============================================================
        # FLIGHT PREFERENCE
        # ============================================================

        preference_match = re.search(
            r"\b(prefer|preference|looking for|want)\s+"
            r"([^.,]+)",
            text,
            re.IGNORECASE
        )

        if preference_match:

            preference_text = (
                preference_match.group(2)
                .strip()
            )

            if (
                "cheap" in preference_text.lower()
                or "cheapest" in preference_text.lower()
            ):
                extracted.preference = "cheap flights"

            elif (
                "non-stop" in preference_text.lower()
                or "nonstop" in preference_text.lower()
            ):
                extracted.preference = "non-stop flights"

        # ============================================================
        # ORIGIN
        # ============================================================

        origin_match = re.search(
            r"\b(?:from|in|currently in|leaving from)\s+"
            r"([A-Za-z][A-Za-z .'-]*?)"
            r"(?=\s+(?:and|want|would|to|for|with|my|i)\b|[,.]|$)",
            text,
            re.IGNORECASE
        )

        if origin_match:

            origin = origin_match.group(1).strip()

            # Avoid accidentally extracting generic words.
            if origin.lower() not in {
                "a",
                "the",
                "there"
            }:
                extracted.origin = origin

        # ============================================================
        # DESTINATION
        # ============================================================

        destination_match = re.search(
            r"\b(?:travel|visit|go|fly)\s+to\s+"
            r"([A-Za-z][A-Za-z .'-]*?)"
            r"(?=\s+(?:for|with|and|my|i|on)\b|[,.]|$)",
            text,
            re.IGNORECASE
        )

        if destination_match:

            destination = (
                destination_match.group(1)
                .strip()
            )

            if destination:
                extracted.destination = destination

        # ============================================================
        # ALTERNATIVE DESTINATION PATTERN
        # ============================================================

        if extracted.destination is None:

            destination_match = re.search(
                r"\bvisit\s+"
                r"([A-Za-z][A-Za-z .'-]*?)"
                r"(?=\s+(?:for|with|and|my|i)\b|[,.]|$)",
                text,
                re.IGNORECASE
            )

            if destination_match:
                extracted.destination = (
                    destination_match.group(1).strip()
                )

        # ============================================================
        # CURRENT LOCATION
        # ============================================================

        current_location_match = re.search(
            r"\bI\s+am\s+in\s+"
            r"([A-Za-z][A-Za-z .'-]*?)"
            r"(?=\s+(?:and|want|would|to|for|with|my|i)\b|[,.]|$)",
            text,
            re.IGNORECASE
        )

        if current_location_match:

            current_location = (
                current_location_match.group(1)
                .strip()
            )

            if current_location:
                extracted.current_location = current_location

        return extracted


    def plan_trip(self, user_request: str):

        # ========================================================
        # FIRST MESSAGE
        # ========================================================

        current_request = self.session.request

        request_is_empty = all(
            getattr(current_request, field.name) is None
            for field in current_request.__dataclass_fields__.values()
        )

        if request_is_empty:

            # ----------------------------------------------------
            # STEP 1: Try local extraction FIRST
            # ----------------------------------------------------

            local_request = self.extract_request_locally(
                user_request
            )

            # ----------------------------------------------------
            # STEP 2: Determine what is still missing
            # ----------------------------------------------------

            self.session.update_request(local_request)

            self.determine_origin()

            request = self.session.request

            missing_fields = self.get_missing_fields()

            # ----------------------------------------------------
            # STEP 3: Only use Gemini if something is missing
            # ----------------------------------------------------

            if missing_fields:

                print("\n===== INITIAL GEMINI REQUEST =====")

                prompt = self.build_prompt(user_request)

                new_request = self.llm.parse_travel_request(
                    prompt
                )

                print("===== INITIAL REQUEST PARSED =====\n")

                self.session.update_request(new_request)

        else:

            # ====================================================
            # FOLLOW-UP MESSAGE
            # ====================================================
            #
            # NO GEMINI CALL HERE.
            # ====================================================

            missing_fields = self.get_missing_fields()

            local_request = self.parse_follow_up_locally(
                user_request,
                missing_fields
            )

            self.session.update_request(
                local_request
            )

        # ========================================================
        # CURRENT REQUEST
        # ========================================================

        request = self.session.request

        # ========================================================
        # DETERMINE ORIGIN
        # ========================================================

        self.determine_origin()

        request = self.session.request

        # ========================================================
        # VALIDATE REQUEST
        # ========================================================

        missing_fields = self.get_missing_fields()

        if missing_fields:

            self.session.missing_fields = missing_fields

            return self.ask_for_missing_information(
                missing_fields
            )

        # Request is now complete.
        self.session.missing_fields = []

        # ========================================================
        # SPECIALIZED AGENTS
        # ========================================================

        flight_result = None
        hotel_result = None
        weather_result = None

        flight_status = "available"
        hotel_status = "available"
        weather_status = "available"

        errors = []

        # --------------------------------------------------------
        # Flight Agent
        # --------------------------------------------------------

        try:

            flight_result = self.flight_agent.search_flights(
                request
            )

        except Exception as e:

            print(f"FlightAgent failed: {e}")

            errors.append(
                f"FlightAgent: Flight service unavailable: {e}"
            )

            flight_result = None
            flight_status = "unavailable"

        # --------------------------------------------------------
        # Hotel Agent
        # --------------------------------------------------------

        try:

            hotel_result = self.hotel_agent.search_hotels(
                request
            )

        except Exception as e:

            print(f"HotelAgent failed: {e}")

            errors.append(
                f"HotelAgent: Hotel service unavailable: {e}"
            )

            hotel_result = None
            hotel_status = "unavailable"

        # --------------------------------------------------------
        # Weather Agent
        # --------------------------------------------------------

        try:

            weather_result = self.weather_agent.get_weather(
                request
            )

        except Exception as e:

            print(f"WeatherAgent failed: {e}")

            errors.append(
                f"WeatherAgent: Weather service unavailable: {e}"
            )

            weather_result = None
            weather_status = "unavailable"

        # ========================================================
        # PURE PYTHON ITINERARY GENERATION
        # ========================================================

        itinerary = []

        try:

            itinerary = self.itinerary_generator.generate(
                request,
                flight_result,
                hotel_result,
                weather_result
            )

        except Exception as e:

            print(f"Itinerary generation failed: {e}")

            errors.append(
                f"Itinerary service unavailable: {e}"
            )

        # ========================================================
        # FINAL TRAVEL PLAN
        # ========================================================

        return TravelPlan(
            destination=request.destination,
            itinerary=itinerary,

            flights=flight_result,
            hotels=hotel_result,
            weather=weather_result,

            flight_status=flight_status,
            hotel_status=hotel_status,
            weather_status=weather_status,

            errors=errors,
        )