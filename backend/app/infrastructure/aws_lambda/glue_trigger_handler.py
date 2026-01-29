import boto3
import json

def handler(event, context):
    glue = boto3.client('glue')
    sagemaker = boto3.client('sagemaker')

    job_name = event.get('glue_job_name', 'feature-engineering-job')
    callback_token = event.get('callback_token')

    try:
        response = glue.start_job_run(JobName=job_name)
        job_run_id = response['JobRunId']

        return {
            "statusCode": 200,
            "body": json.dumps({
                "glue_job_run_id": job_run_id,
                "status": "Started"
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": str(e)
        }