import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any
from app.models import ActivityFactory
from app.engines.training_engine import TrainingEngine


class ActivityModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    sub_sport: str | None = None
    timestamp: datetime | None = None
    duration_min: float = 0.0
    avg_heart_rate: float | int = 0.0
    altitude: List[float | None] | None = None
    speed: List[float | None] | None = None
    watts: List[float | None] | None = None
    distance: float = 0.0
    calories: float | int | None = None
    temperature: List[float | None] | None = None
    cadence: List[float | None] | None = None
    power: List[float | None] | None = None
    heart_rate: List[int | None] | None = None
    enhanced_altitude: List[float | None] | None = None
    enhanced_speed: List[float | None] | None = None
    trimp: float = 0.0


class AnalysisResult(BaseModel):
    activities: List[ActivityModel]
    metrics: List[Dict[str, Any]]


# Global cache to store the calculated results
cache = {"activities": [], "metrics": []}


def serialize_activity(activity) -> ActivityModel:
    return ActivityModel.model_validate(activity)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Calculate everything on startup and cache it
    folder_path = "./sandbox"
    if os.path.exists(folder_path):
        files = [f for f in os.listdir(folder_path) if f.endswith(".fit")]
        activities_list = []
        for file in files:
            path = os.path.join(folder_path, file)
            activity_obj = ActivityFactory.create_activity(path)
            if activity_obj:
                activities_list.append(activity_obj)

        # Engine
        engine = TrainingEngine(activities_list)
        metrics_df = engine.get_training_metrics()

        # Format metrics
        metrics_records = []
        if not metrics_df.empty:
            # metrics_df has 'date' as index, so we should reset_index
            metrics_df_reset = metrics_df.reset_index()
            # Convert datetime to string
            metrics_df_reset["date"] = metrics_df_reset["date"].dt.strftime("%Y-%m-%d")
            metrics_records = metrics_df_reset.to_dict(orient="records")

        cache["activities"] = activities_list
        cache["metrics"] = metrics_records

    yield
    # Clean up on shutdown
    cache.clear()


app = FastAPI(lifespan=lifespan)


@app.get("/api/single-activity/{file_name}", response_model=ActivityModel)
def get_single_activity(file_name: str):
    for activity in cache["activities"]:
        if activity.name == file_name:
            return serialize_activity(activity)
    raise HTTPException(status_code=404, detail="Activity not found")


@app.get("/api/analysis", response_model=AnalysisResult)
def get_analysis():
    return {
        "activities": [
            serialize_activity(activity) for activity in cache["activities"]
        ],
        "metrics": cache["metrics"],
    }
