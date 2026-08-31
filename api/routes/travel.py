from fastapi import APIRouter, HTTPException

from api.schemas.travel import (
    TravelRequestSchema,
    TravelPlanResponse,
)

from app.composition import create_local_service


router = APIRouter(
    prefix="/travel",
    tags=["Travel"],
)


travel_service = create_local_service()


@router.post("/plan")
def plan_trip(request: TravelRequestSchema):

    if request.message:
        prompt = request.message
    else:
        prompt = f"""
        Plan a trip using the following travel requirements:

        Current location: {request.current_location}
        Origin: {request.origin}
        Destination: {request.destination}
        Days: {request.days}
        Budget: {request.budget}
        Travelers: {request.travelers}
        Preference: {request.preference}
        """

    try:
        result = travel_service.plan_trip(prompt)

        # --------------------------------------------------------
        # Incomplete request:
        # RootTravelAgent returns a follow-up question.
        # --------------------------------------------------------
        if isinstance(result, str):
            return {
                "message": result,
            }

        # --------------------------------------------------------
        # Completed request:
        # Preserve the existing API response structure.
        # --------------------------------------------------------
        return TravelPlanResponse.model_validate(
            result,
            from_attributes=True,
        )

    except Exception as exc:
        print(f"Travel planning failed: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Travel planning failed.",
        ) from exc