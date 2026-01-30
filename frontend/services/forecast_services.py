from importlib.resources import files
from urllib import response
from .api_client import APIClient
import requests

class ForecastService:
    def __init__(self):
        self.client = APIClient()

    def upload_data(self, uploaded_files):
        files = [
        ("files", (file.name, file.getvalue(), file.type)) 
        for file in uploaded_files
        ]
        try:
            response = self.client.post_file("/upload-raw-data", files=files)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Error uploading data: {e}")
            return None
    
    def trigger_train(self):
        try:
            response = self.client.post_json("/train", json_data={})
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Error triggering train: {e}")
            return None
    
    def batch_prediction(self, model_arn, input_path):
        payload = {
            "model_arn": model_arn,
            "input_s3_path": input_path
        }
        try:
            response = self.client.post_json("/predict", json_data=payload)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Error batch prediction: {e}")
            return None
    
    def get_s3_inputs(self):
        try:
            response = self.client.get_json("/s3-inputs")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Error getting S3 inputs: {e}")
            return None
    
    def stream_train_progress(self, execution_arn):
        try:
            url = f"{self.client.forecast_url}/train-progress/{execution_arn}"
            return requests.get(url, stream=True)
        except Exception as e:
            print(f"Error streaming train progress: {e}")
            return None
    
    def stream_prediction_progress(self, job_name):
        try:
            url = f"{self.client.forecast_url}/prediction-progress/{job_name}"
            return requests.get(url, stream=True)
        except Exception as e:
            print(f"Error streaming prediction progress: {e}")
            return None
    
    def get_prediction_results(self, job_name):
        try:
            response = self.client.get_json(f"/prediction-results/{job_name}")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Error getting prediction results: {e}")
            return None