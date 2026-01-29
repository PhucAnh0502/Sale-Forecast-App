import boto3
import os
from fastapi import HTTPException

class ModelService:
    def __init__(self):
        self.sm_client = boto3.client('sagemaker')
        self.group_name = "SalesForecastGroup"

    async def list_pending_models(self):
        try:
            response = self.sm_client.list_model_packages(
                ModelPackageGroupName=self.group_name,
                ModelApprovalStatus='PendingManualApproval',
                SortBy='CreationTime',
                SortOrder='Descending'
            )

            pending_models = [
                {
                    "name": m['ModelPackageName'],
                    "version": m['ModelPackageVersion'],
                    "arn": m['ModelPackageArn'],
                    "creation_time": m['CreationTime'].strftime("%Y-%m-%d %H:%M:%S")
                }
                for m in response['ModelPackageSummaryList']
            ]
            return {"pending_models": pending_models}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    async def update_model_status(self, model_arn: str, status: str, comment: str):
        try:
            response = self.sm_client.update_model_package(
                ModelPackageArn=model_arn,
                ModelApprovalStatus=status,
                ApprovalDescription=comment
            )
            return {
                "status": "success",
                "message": f"Model {status}",
                "details": response
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))