import joblib
import tarfile
import os
import json
import pandas as pd
import awswrangler as wr
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

def handler():
    model_path = "opt/ml/processing/model/model.tar.gz"
    with tarfile.open(model_path) as tar:
        tar.extractall(path=".")

    model = joblib.load("model.joblib")

    test_path = "opt/ml/processing/test/"
    df_test = wr.s3.read_parquet(path=test_path)

    X_test = df_test.drop(columns=['sales'])
    y_test = df_test['sales']

    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100

    report_dict = {
        "regression_metrics": {
            "mse": {"value": mse},
            "mae": {"value": mae},
            "r2": {"value": r2},
            "mape": {"value": mape}
        },
        "feature_importance": model.get_booster().get_score(importance_type='weight')
    }

    output_dir = "opt/ml/processing/evaluation/"
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "evaluation.json"), "w") as f:
        f.write(json.dumps(report_dict))

if __name__ == "__main__":
    handler()