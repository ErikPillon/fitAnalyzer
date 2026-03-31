from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
from pydantic import BaseModel
from typing import List, Dict, Any
from app.models import ActivityFactory
from app.engines.training_engine import TrainingEngine

class ActivityModel(BaseModel):
    name: str
    timestamp: str
    duration_min: float
    avg_heart_rate: float
    trimp: float

class AnalysisResult(BaseModel):
    activities: List[ActivityModel]
    metrics: List[Dict[str, Any]]

# Global cache to store the calculated results
cache = {
    "activities": [],
    "metrics": []
}

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
        
        # Format activities for Pydantic
        act_models = []
        for act in activities_list:
            act_models.append(ActivityModel(
                name=act.name,
                timestamp=act.timestamp.isoformat(),
                duration_min=act.duration_min,
                avg_heart_rate=act.avg_heart_rate or 0.0,
                trimp=act.trimp
            ))
            
        # Format metrics
        metrics_records = []
        if not metrics_df.empty:
            # metrics_df has 'date' as index, so we should reset_index
            metrics_df_reset = metrics_df.reset_index()
            # Convert datetime to string
            metrics_df_reset['date'] = metrics_df_reset['date'].dt.strftime('%Y-%m-%d')
            metrics_records = metrics_df_reset.to_dict(orient="records")
            
        cache["activities"] = act_models
        cache["metrics"] = metrics_records
        
    yield
    # Clean up on shutdown
    cache.clear()

app = FastAPI(lifespan=lifespan)

@app.get("/api/analysis", response_model=AnalysisResult)
def get_analysis():
    return {"activities": cache["activities"], "metrics": cache["metrics"]}
