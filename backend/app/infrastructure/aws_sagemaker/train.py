import pandas as pd
import awswrangler as wr
import xgboost as xgb
import argparse
import os
import joblib

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR')) # S3 path to save the model
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN')) # S3 path to training data
    args = parser.parse_args()

    df = wr.s3.read_parquet(path=args.train)

    X=df.drop(columns=['sales'])
    y=df['sales']

    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100)
    model.fit(X, y)

    model_path = os.path.join(args.model_dir, "model.tar.gz")
    joblib.dump(model, os.path.join(args.model_dir, "model.joblib"))
    print(f"Model saved to {model_path}")


if __name__ == "__main__":
    main()