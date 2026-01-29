from importlib.resources import files
from urllib import response
from .api_client import APIClient

class ForecastService:
    def __init__(self):
        self.client = APIClient()

    def upload_data(self, uploaded_files):
        files = [
        ("files", (file.name, file.getvalue(), file.type)) 
        for file in uploaded_files
        ]
        response = self.client.post_file("/upload-raw-data", files=files)
        return response.json() if response.status_code == 200 else None
    
    def trigger_train(self):
        response = self.client.post_json("/train", json_data={})
        return response.json() if response.status_code == 200 else None
    
    def batch_prediction(self, model_arn, input_path):
        payload = {
            "model_arn": model_arn,
            "input_s3_path": input_path
        }
        response = self.client.post_json("/predict", json_data=payload)
        return response.json() if response.status_code == 200 else None