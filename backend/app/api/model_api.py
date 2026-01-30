from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.model_service import ModelService

router = APIRouter()

def get_model_service():
    return ModelService()

class ModelRequest(BaseModel):
    model_package_arn: str

@router.get("/pending")
async def list_pending_models(service: ModelService = Depends(get_model_service)):
    return await service.list_pending_models()

@router.get("/approved")
async def list_approved_models(service: ModelService = Depends(get_model_service)):
    return await service.list_approved_models()

@router.post("/approve")
async def approve_model(request: ModelRequest, service: ModelService = Depends(get_model_service)):
    return await service.update_model_status(
        model_arn=request.model_package_arn,
        status='Approved',
        comment='Model manually approved.'
    )

@router.post("/reject")
async def reject_model(request: ModelRequest, service: ModelService = Depends(get_model_service)):
    return await service.update_model_status(
        model_arn=request.model_package_arn,
        status='Rejected',
        comment='Model manually rejected.'
    )

@router.get("/metrics/{model_package_arn:path}")
async def get_model_metrics(model_package_arn: str, service: ModelService = Depends(get_model_service)):
    return await service.get_model_metrics(model_package_arn)