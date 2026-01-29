import boto3
import os
import logging
import pandas as pd
import awswrangler as wr
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    processed_bucket = os.environ.get("S3_PROCESSED_DATA_BUCKET")

    try:
        message = json.loads(event['Records'][0]['Sns']['Message'])
        job_id = message['jobId']
        status = message['status']

        if status != 'SUCCEEDED':
            logger.error(f"Textract job {job_id} failed with status: {status}")
            return
        
        df_list = wr.textract.get_document_analysis(job_id=job_id)

        if not df_list:
            logger.warning(f"No tables found in Textract job {job_id}")
            return
        
        final_df = pd.concat(df_list, ignore_index=True)
        target_path = f"s3://{processed_bucket}/{job_id}.parquet"

        wr.s3.to_parquet(
            df=final_df,
            path=target_path,
            index=False
        )

        return {"status": "SUCCEEDED", "path": target_path}
    except Exception as e:
        logger.error(f"Error processing Textract job: {str(e)}")
        return {"status": "FAILED", "error": str(e)}