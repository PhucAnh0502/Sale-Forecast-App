from .api_client import APIClient

class ModelService:
    def __init__(self):
        self.client = APIClient()

    def get_pending_models(self):
        response = self.client.get_json("/pending", is_model=True)
        return response.json() if response.status_code == 200 else []
    
    def get_approved_models(self):
        response = self.client.get_json("/approved", is_model=True)
        return response.json() if response.status_code == 200 else []
    
    def approve_model(self, model_arn, comment):
        payload = {
            "model_package_arn": model_arn,
            "comment": comment
        }
        response = self.client.post_json("/approve", json_data=payload, is_model=True)
        return response.status_code == 200
    
    def reject_model(self, model_arn, comment):
        payload = {
            "model_package_arn": model_arn,
            "comment": comment
        }
        response = self.client.post_json("/reject", json_data=payload, is_model=True)
        return response.status_code == 200