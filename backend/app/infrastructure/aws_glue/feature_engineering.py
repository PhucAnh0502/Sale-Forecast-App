import sys
import awswrangler as wr
import pandas as pd
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from sklearn.model_selection import train_test_split

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'PROCESSED_DATA_BUCKET', 'FEATURED_STORE_BUCKET'])
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

PROCESSED_DATA_BUCKET_PATH = f"s3://{args['PROCESSED_DATA_BUCKET']}/"
FEATURE_STORE_BUCKET_PATH = f"s3://{args['FEATURED_STORE_BUCKET']}/"

def run_etl():
    df = wr.s3.read_parquet(path=PROCESSED_DATA_BUCKET_PATH)

    # Data Cleaning

    # Feature Engineering

    train_df, test_df = train_test_split(df, test_size=0.2, shuffle=False)
    wr.s3.to_parquet(
        df=train_df,
        path=f"{FEATURE_STORE_BUCKET_PATH}train/",
        dataset=True,
        mode="append",
    )

    wr.s3.to_parquet(
        df=test_df,
        path=f"{FEATURE_STORE_BUCKET_PATH}test/",
        dataset=True,
        mode="append",
    )

if __name__ == "__main__":
    run_etl() 