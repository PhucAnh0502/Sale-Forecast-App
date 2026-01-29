import awswrangler as wr
import boto3
import os
import logging
import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

textract_client = boto3.client('textract')
s3_client = boto3.client('s3')

def handler(event, context):
    processed_bucket = os.environ.get('S3_PROCESSED_DATA_BUCKET')

    try:
        bucket_raw = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
        path = f"s3://{bucket_raw}/{key}"
        file_extension = os.path.splitext(key)[1].lower()

        if file_extension == '.pdf':
            return trigger_textract(bucket_raw, key)
        
        elif file_extension in ['.csv', '.xlsx']:
            return process_structured_data(path, processed_bucket, key, file_extension)
        
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return {"status": "FAILED", "error": str(e)}
    
def trigger_textract(bucket, key):
    logger.info(f"Triggering Textract for file: s3://{bucket}/{key}")

    response = textract_client.start_document_analysis(
        DocumentLocation={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        },
        FeatureTypes=['TABLES', 'FORMS'],
        NotificationChannel={
            'RoleArn': os.environ.get('TEXTRACT_SNS_ROLE_ARN'),
            'SNSTopicArn': os.environ.get('SNS_TOPIC_ARN')
        }
    )

    logger.info(f"Textract job started with JobId: {response['JobId']}")
    return {
        "status": "SUCCEEDED", 
        "jobId": response['JobId'], 
        "file" : key
    }

def process_structured_data(s3_path, processed_bucket, original_key, file_extension):
    logger.info(f"Processing structured data file: {s3_path}")
    if file_extension == '.csv':
        df = wr.s3.read_csv(s3_path)
    elif file_extension == '.xlsx':
        df = wr.s3.read_excel(s3_path)
    else:
        raise ValueError(f"Unsupported structured data file type: {file_extension}")
    
    filename = os.path.basename(original_key).replace(file_extension, '.parquet')
    target_path = f"s3://{processed_bucket}/{filename}"

    wr.s3.to_parquet(
        df=df,
        path=target_path,
        index=False
    )

    logger.info(f"File converted and saved to: {target_path}")
    return {
        "status": "PROCESSED",
        "processed_file": target_path
    }