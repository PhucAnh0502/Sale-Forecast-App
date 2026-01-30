import boto3
import os
from fastapi import HTTPException
import json

class ModelService:
    def __init__(self):
        self.group_name = "SalesForecastGroup"
        self.sm_client = boto3.client('sagemaker', region_name=os.getenv('AWS_REGION', 'us-east-1'))

    async def list_pending_models(self):
        try:
            response = self.sm_client.list_model_packages(
                ModelPackageGroupName=self.group_name,
                ModelApprovalStatus='PendingManualApproval',
                SortBy='CreationTime',
                SortOrder='Descending'
            )
            pending_models = []

            for m in response['ModelPackageSummaryList']:
                arn = m['ModelPackageArn']
                metrics = await self.get_model_metrics(arn)

                pending_models.append({
                    "name": m['ModelPackageName'],
                    "version": m['ModelPackageVersion'],
                    "arn": arn,
                    "creation_time": m['CreationTime'].strftime("%Y-%m-%d %H:%M:%S"),
                    "metrics": metrics
                })
            return {"pending_models": pending_models}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    async def list_approved_models(self):
        try:
            response = self.sm_client.list_model_packages(
                ModelPackageGroupName=self.group_name,
                ModelApprovalStatus='Approved',
                SortBy='CreationTime',
                SortOrder='Descending'
            )

            approved_models = [
                {
                    "name": m['ModelPackageName'],
                    "version": m['ModelPackageVersion'],
                    "arn": m['ModelPackageArn'],
                    "creation_time": m['CreationTime'].strftime("%Y-%m-%d %H:%M:%S")
                }
                for m in response['ModelPackageSummaryList']
            ]
            return {"approved_models": approved_models}
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
        
    async def get_pipeline_steps_status(self, execution_arn: str):
        try:
            response = self.sm_client.list_pipeline_execution_steps(
                PipelineExecutionArn=execution_arn,
                SortOrder='Ascending'
            )

            steps = []
            for step in response.get('PipelineExecutionSteps', []):
                steps.append({
                    "step_name": step['StepName'],
                    "step_status": step['StepStatus'],
                    "start_time": step['StartTime'].strftime("%Y-%m-%d %H:%M:%S") if 'StartTime' in step else None,
                    "end_time": step['EndTime'].strftime("%Y-%m-%d %H:%M:%S") if 'EndTime' in step else None,
                })

            execution_info = self.sm_client.describe_pipeline_execution(
                PipelineExecutionArn=execution_arn
            )

            return {
                "overall_status": execution_info['PipelineExecutionStatus'],
                "steps": steps
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    async def get_model_metrics(self, model_package_arn: str):
        try:
            response = self.sm_client.describe_model_package(
                ModelPackageName=model_package_arn
            )

            metrics_s3_uri = response.get('ModelMetrics', {}).get('ModelStatistics', {}).get('S3Uri')

            if not metrics_s3_uri:
                return {"message": "No metrics found for this model."}
            
            path_parts = metrics_s3_uri.replace("s3://", "").split("/", 1)
            bucket = path_parts[0]
            key="/".join(path_parts[1:])

            s3_client = boto3.client('s3')
            s3_res = s3_client.get_object(Bucket=bucket, Key=key)
            content = s3_res['Body'].read().decode('utf-8')

            return json.loads(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))