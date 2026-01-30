import asyncio
import json
import os
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from pydantic import BaseModel
from app.services.forecast_service import ForecastService
from typing import List
from app.services.model_service import ModelService
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

def get_forecast_service():
    return ForecastService()

def get_model_service():
    return ModelService()

class PredictRequest(BaseModel):
    model_arn: str
    input_s3_path: str

@router.post("/upload-raw-data")
async def upload(files: List[UploadFile] = File(...), service: ForecastService = Depends(get_forecast_service)):
    uploaded_urls = []
    for file in files:
        s3_url = await service.upload_raw_data(file.filename, await file.read())
        uploaded_urls.append({"filename": file.filename, "s3_uri": s3_url})
    return {"message": f"Successfully uploaded {len(uploaded_urls)} files", "data": uploaded_urls}

@router.post("/train")
async def train(service: ForecastService = Depends(get_forecast_service)):
    execution_arn = await service.trigger_training_pipeline()
    return {"message": "Pipeline started", "execution_arn": execution_arn}

@router.post("/predict")
async def predict(request: PredictRequest, service: ForecastService = Depends(get_forecast_service)):
    job_info = await service.execute_batch_prediction(request.model_arn, request.input_s3_path)
    return {"message": "Prediction job created", "details": job_info}

@router.get("/s3-inputs")
async def list_s3_inputs(service: ForecastService = Depends(get_forecast_service)):
    s3_inputs = await service.list_s3_inputs()
    return {"s3_inputs": s3_inputs}

@router.get("/train-progress/{execution_arn}")
async def train_progress(execution_arn: str, service: ModelService = Depends(get_model_service)):
    async def event_generator():
        while True:
            data = await service.get_pipeline_steps_status(execution_arn)
            yield {
                "event": "update",
                "data": json.dumps(data)
            }

            if data['overall_status'] in ['Succeeded', 'Failed', 'Stopped']:
                break

            await asyncio.sleep(5)
    
    return EventSourceResponse(event_generator())

@router.get("/prediction-progress/{job_name}")
async def prediction_progress(job_name: str, service: ForecastService = Depends(get_forecast_service)):
    """Stream prediction job progress"""
    async def event_generator():
        # Real AWS implementation would poll SageMaker transform job status
        while True:
            # TODO: Implement real transform job status check
            yield {
                "event": "update",
                "data": json.dumps({"status": "Running", "message": "Checking job status..."})
            }
            await asyncio.sleep(5)
            break
    
    return EventSourceResponse(event_generator())

@router.get("/prediction-results/{job_name}")
async def get_prediction_results(job_name: str, service: ForecastService = Depends(get_forecast_service)):
    """Get prediction results for a completed job"""
    # Real AWS implementation would read results from S3
    raise HTTPException(status_code=501, detail="Real implementation not yet available")
