from abc import ABC, abstractmethod

class IAWSManager(ABC):
    @abstractmethod
    def upload_to_s3(self, file_content, filename): pass

    @abstractmethod
    def start_textract_job(self, s3_key): pass

    @abstractmethod
    def trigger_sagemaker_training(self, training_data_uri): pass