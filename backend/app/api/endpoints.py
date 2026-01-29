from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from pydantic import BaseModel
from app.services.forecast_service import ForecastService

router = APIRouter()

def get_forecast_service():
    return ForecastService()

class PredictRequest(BaseModel):
    model_arn: str
    input_s3_path: str

@router.post("/upload-raw-data")
async def upload(file: UploadFile = File(...), service: ForecastService = Depends(get_forecast_service)):
    content = await file.read()
    s3_uri = await service.upload_raw_data(content, file.filename)
    return {"message": "Upload successful", "s3_uri": s3_uri}

@router.post("/train")
async def train(service: ForecastService = Depends(get_forecast_service)):
    execution_arn = await service.trigger_training_pipeline()
    return {"message": "Pipeline started", "execution_arn": execution_arn}

@router.post("/predict")
async def predict(request: PredictRequest, service: ForecastService = Depends(get_forecast_service)):
    job_info = await service.execute_batch_prediction(request.model_arn, request.input_s3_path)
    return {"message": "Prediction job created", "details": job_info}