from fastapi import FastAPI

from api.routes.travel import router as travel_router


app = FastAPI(
    title="AI Travel Planner",
    description="AI-powered travel planning API",
    version="1.0.0",
)


app.include_router(travel_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }