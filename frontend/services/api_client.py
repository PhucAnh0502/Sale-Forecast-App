import requests
import os
from dotenv import load_dotenv

load_dotenv()
class APIClient:
    def __init__(self):
        self.forecast_url = f"{os.getenv('API_BASE_URL')}/forecast"
        self.model_url = f"{os.getenv('API_BASE_URL')}/model"
        
    def post_file(self, endpoint, files, is_model=False):
        url = self.model_url if is_model else self.forecast_url
        return requests.post(f"{url}{endpoint}", files=files)
    
    def post_json(self, endpoint, json_data, is_model=False):
        url = self.model_url if is_model else self.forecast_url
        return requests.post(f"{url}{endpoint}", json=json_data)
    
    def get_json(self, endpoint, is_model=False):
        url = self.model_url if is_model else self.forecast_url
        return requests.get(f"{url}{endpoint}")