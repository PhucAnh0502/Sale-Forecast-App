import os
import boto3
from app.infrastructure.aws_sagemaker.pipeline_orchestrator import PipelineOrchestrator
from app.infrastructure.aws_sagemaker.batch_predict import BatchPredictor

class ForecastService:
    def __init__(self):
        self.raw_data_bucket = os.getenv('S3_RAW_DATA_BUCKET')
        self.artifact_bucket = os.getenv('S3_ARTIFACTS_BUCKET')
        self.feature_store_bucket = os.getenv('S3_FEATURE_STORE_BUCKET')
        
        self.s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.pipeline_orchestrator = PipelineOrchestrator()
        self.batch_predictor = BatchPredictor()

    async def upload_raw_data(self, file_name, file_content):
        file_key = f'uploads/{file_name}'
        self.s3_client.put_object(Bucket=self.raw_data_bucket, Key=file_key, Body=file_content)
        return f"s3://{self.raw_data_bucket}/{file_key}"
    
    async def trigger_training_pipeline(self):
        pipeline_name = "Sale-Forecast-ML-Pipeline"
        s3_fs_uri = f's3://{self.feature_store_bucket}'

        self.pipeline_orchestrator.create_pipeline(pipeline_name, s3_fs_uri)
        execution_arn = self.pipeline_orchestrator.start_pipeline(pipeline_name)
        return execution_arn
    
    async def execute_batch_prediction(self, model_arn, input_path):
        import time
        output_path = f's3://{self.artifact_bucket}/predictions/{int(time.time())}/'
        job_info = self.batch_predictor.run_transform_job(
            model_package_arn=model_arn,
            input_s3_uri=input_path,
            output_s3_uri=output_path
        )
        return job_info
    
    async def list_s3_inputs(self):
        response = self.s3_client.list_objects_v2(Bucket=self.feature_store_bucket, Prefix='/')
        s3_inputs = []
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_inputs.append(f"s3://{self.feature_store_bucket}/{obj['Key']}")
        return s3_inputs