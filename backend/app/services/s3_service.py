import os
import boto3
from fastapi import HTTPException
import base64

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-1'))

    async def list_bucket_files(self, bucket_type: str):
        env_mapping = {
            "raw": "S3_RAW_DATA_BUCKET",
            "processed": "S3_PROCESSED_DATA_BUCKET",
            "feature-store": "S3_FEATURE_STORE_DATA_BUCKET",
            "artifacts": "S3_ARTIFACTS_BUCKET"
        }
        
        env_var_name = env_mapping.get(bucket_type.lower(), f"S3_{bucket_type.upper().replace('-', '_')}_BUCKET")
        bucket_name = os.getenv(env_var_name)

        if not bucket_name:
            raise HTTPException(status_code=500, detail=f"Environment variable {env_var_name} is not configured")

        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        "filename": obj['Key'],
                        "size": f"{obj['Size'] / 1024:.2f} KB",
                        "last_modified": obj['LastModified'].strftime("%Y-%m-%d %H:%M:%S")
                    })
            return files
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    async def list_s3_inputs(self):
        env_var_name = "S3_FEATURE_STORE_DATA_BUCKET"
        bucket_name = os.getenv(env_var_name)
        
        if not bucket_name:
            raise HTTPException(status_code=500, detail=f"Environment variable {env_var_name} is not configured")
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix='/')
            s3_inputs = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    s3_inputs.append(f"s3://{bucket_name}/{obj['Key']}")
            return s3_inputs
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    async def get_file_content(self, bucket_type: str, file_key: str):
        env_mapping = {
            "raw": "S3_RAW_DATA_BUCKET",
            "processed": "S3_PROCESSED_DATA_BUCKET",
            "feature-store": "S3_FEATURE_STORE_DATA_BUCKET",
            "artifacts": "S3_ARTIFACTS_BUCKET"
        }
        
        env_var_name = env_mapping.get(bucket_type.lower())
        bucket_name = os.getenv(env_var_name)
        if not bucket_name:
            raise HTTPException(status_code=500, detail=f"Environment variable {env_var_name} is not configured")

        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)
            raw_data = response['Body'].read()
            return base64.b64encode(raw_data).decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))