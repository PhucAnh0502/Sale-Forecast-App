from .api_client import APIClient

class S3Service:
    def __init__(self):
        self.client = APIClient()

    def get_bucket_files(self, bucket_type):
        try:
            response = self.client.get_json(f"/list-files/{bucket_type}")
            return response.json().get("files", []) if response.status_code == 200 else []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_s3_inputs(self):
        try:
            response = self.client.get_json("/s3-inputs")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Error getting S3 inputs: {e}")
            return None
        
    def get_file_content(self, bucket_type, file_key):
        try:
            response = self.client.get_json(f"/file-content?bucket_type={bucket_type}&file_key={file_key}")
            return response.json().get("content") if response.status_code == 200 else None
        except Exception as e:
            print(f"Error getting file content: {e}")
            return None