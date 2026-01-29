import boto3
import os
import logging
import time

logger = logging.getLogger(__name__)

class BatchPredictor:
    def __init__(self, region_name):
        self.sm_client = boto3.client('sagemaker', region_name=region_name)

    def run_transform_job(self, model_package_arn, input_s3_uri, output_s3_uri):
        model_name = f"forecast-model-{int(time.time())}"

        logger.info(f"Creating model {model_name}")
        self.sm_client.create_model(
            ModelName=model_name,
            Containers=[{
                'ModelPackageName': model_package_arn,
            }],
            ExecutionRoleArn=os.environ['SM_ROLE_ARN']
        )

        transform_job_name = f"Batch-Transform-{int(time.time())}"

        logger.info(f"Starting transform job {transform_job_name}")

        self.sm_client.create_transform_job(
            TransformJobName=transform_job_name,
            ModelName=model_name,
            MaxConcurrentTransforms=1,
            ModelClientConfig={
                'InvocationsTimeoutInSeconds': 3600,
                'InvocationsMaxRetries': 3
            },
            TransformInput={
                'DataSource': {
                    'S3DataSource': {
                        'S3DataType': 'S3Prefix',
                        'S3Uri': input_s3_uri
                    }
                },
                'ContentType': 'application/x-parquet',
                'SplitType': 'None'
            },
            TransformOutput={
                'S3OutputPath': output_s3_uri,
                'AssembleWith': 'Line',
                'Accept': 'text/csv'
            },
            TransformResources={
                'InstanceType': 'ml.m5.xlarge',
                'InstanceCount': 1
            }
        )

        return {
            "TransformJobName": transform_job_name,
            "ModelName": model_name,
            "OutputS3": output_s3_uri
        }
    
    def check_status(self, job_name):
        response = self.sm_client.describe_transform_job(TransformJobName=job_name)
        status = response['TransformJobStatus']
        logger.info(f"Transform job {job_name} status: {status}")
        return status

def batch_predict(region_name, model_package_arn, input_s3_uri, output_s3_uri):
    predictor = BatchPredictor(region_name)
    return predictor.run_transform_job(
        model_package_arn=model_package_arn,
        input_s3_uri=input_s3_uri,
        output_s3_uri=output_s3_uri,
    )