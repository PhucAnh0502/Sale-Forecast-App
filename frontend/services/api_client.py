import requests
import os

class APIClient:
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL")
        
    def post_file(self, endpoint, files):
        return requests.post(f"{self.base_url}/{endpoint}", files=files)
    
    def post_json(self, endpoint, json_data):
        return requests.post(f"{self.base_url}/{endpoint}", json=json_data)