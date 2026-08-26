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


@router.post("/plan", response_model=TravelPlanResponse)
def plan_trip(request: TravelRequestSchema):

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
        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Travel planning failed.",
        ) from exc