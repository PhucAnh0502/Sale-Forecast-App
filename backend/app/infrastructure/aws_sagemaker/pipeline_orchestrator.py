import os
import boto3

def _import_sagemaker():
    try:
        from sagemaker.workflow.pipeline_context import PipelineSession
        from sagemaker.workflow.model_step import ModelStep
        from sagemaker.workflow.steps import TrainingStep, ProcessingStep
        from sagemaker.workflow.pipeline import Pipeline
        from sagemaker.workflow.properties import PropertyFile
        from sagemaker.workflow.lambda_step import LambdaStep, LambdaOutput, LambdaOutputTypeEnum
        from sagemaker.lambda_helper import Lambda
        from sagemaker.xgboost.estimator import XGBoost
        from sagemaker.inputs import TrainingInput
        from sagemaker.model import Model
        from sagemaker.processing import ScriptProcessor, ProcessingInput, ProcessingOutput
        from sagemaker.model_metrics import MetricsSource, ModelMetrics
    except Exception as exc:
        raise RuntimeError(
            "SageMaker SDK is required for pipeline operations. Install it with 'pip install sagemaker'."
        ) from exc

    return (
        PipelineSession,
        ModelStep,
        TrainingStep,
        ProcessingStep,
        Pipeline,
        PropertyFile,
        XGBoost,
        TrainingInput,
        Model,
        ScriptProcessor,
        ProcessingInput,
        ProcessingOutput,
        MetricsSource,
        ModelMetrics,
        LambdaStep,
        LambdaOutput,
        LambdaOutputTypeEnum,
        Lambda,
    )

class PipelineOrchestrator:
    def __init__(self, region):
        self.region = region
        self.role = os.environ.get('SM_ROLE_ARN')
        self.bucket = os.environ.get('S3_ARTIFACTS_BUCKET')
        (PipelineSession, *_rest) = _import_sagemaker()
        self.pipeline_session = PipelineSession()

    def create_pipeline(self, pipeline_name, s3_feature_store_uri):
        (
            _PipelineSession,
            ModelStep,
            TrainingStep,
            ProcessingStep,
            Pipeline,
            PropertyFile,
            XGBoost,
            TrainingInput,
            Model,
            ScriptProcessor,
            ProcessingInput,
            ProcessingOutput,
            MetricsSource,
            ModelMetrics,
            LambdaStep,
            LambdaOutput,
            LambdaOutputTypeEnum,
            Lambda,
        ) = _import_sagemaker()

        func_glue_trigger = Lambda(
            function_arn=os.environ.get('GLUE_TRIGGER_LAMBDA_ARN'),
        )

        step_glue = LambdaStep(
            name="TriggerGlueFeatureEngineering",
            lambda_func=func_glue_trigger,
            inputs={
                "glue_job_name": "feature-engineering-job",
            },
            outputs=[
                LambdaOutput(
                    output_name="status",
                    output_type=LambdaOutputTypeEnum.String
                )
            ]
        )

        xgb_train = XGBoost(
            entry_point="train.py",
            source_dir="backend/app/infrastructure/aws_sagemaker",
            role=self.role,
            instance_count=1,
            instance_type="ml.m5.xlarge",
            framework_version="1.5-1",
            output_path=f"s3://{self.bucket}/models/",
            sagemaker_session=self.pipeline_session,
        )

        step_train = TrainingStep(
            name="SaleForecastTraining",
            estimator=xgb_train,
            inputs={
                "train": TrainingInput(
                    s3_data=f"{s3_feature_store_uri}/train/",
                    content_type="application/x-parquet"
                )
            },
            depends_on=[step_glue]
        )

        script_eval = ScriptProcessor(
            image_uri=xgb_train.image_uri,
            command=["python3"],
            instance_type="ml.m5.xlarge",
            instance_count=1,
            base_job_name="script-eval",
            role=self.role,
            sagemaker_session=self.pipeline_session,
        )

        evaluation_report = PropertyFile(
            name="EvaluationReport",
            output_name="evaluation",
            path="evaluation.json",
        )

        step_eval = ProcessingStep(
            name="EvaluateSaleModel",
            processor=script_eval,
            inputs=[
                ProcessingInput(
                    source=step_train.properties.ModelArtifacts.S3ModelArtifacts,
                    destination="/opt/ml/processing/model/"
                ),
                ProcessingInput(
                    source=f"{s3_feature_store_uri}/test/",
                    destination="/opt/ml/processing/test/"
                )
            ],
            outputs=[
                ProcessingOutput(
                    output_name="evaluation",
                    source="/opt/ml/processing/evaluation/"
                )
            ],
            code="backend/app/infrastructure/aws_sagemaker/evaluate.py",
            property_files=[evaluation_report],
        )

        model_metrics = ModelMetrics(
            model_statistics=MetricsSource(
                s3_uri=f"{step_eval.arguments['ProcessingOutputConfig']['Outputs'][0]['S3Output']['S3Uri']}/evaluation.json",
                content_type="application/json"
            )
        )

        model = Model(
            image_uri=xgb_train.image_uri,
            model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
            role=self.role,
            sagemaker_session=self.pipeline_session,
        )

        step_register = ModelStep(
            name="RegisterSaleModel",
            step_args=model.register(
                content_types=["text/csv"],
                response_types=["text/csv"],
                inference_instances=["ml.m5.xlarge"],
                transform_instances=["ml.m5.xlarge"],
                model_package_group_name="SalesForecastGroup",
                approval_status="PendingManualApproval",
                model_metrics=model_metrics,
            ),
        )

        pipeline = Pipeline(
            name=pipeline_name,
            steps=[step_glue, step_train, step_eval, step_register],
            sagemaker_session=self.pipeline_session,
        )

        pipeline.upsert(role_arn=self.role)
        return pipeline
    
    def start_pipeline(self, pipeline_name):
        sm_client = boto3.client('sagemaker')
        response = sm_client.start_pipeline_execution(
            PipelineName=pipeline_name
        )
        return response["PipelineExecutionArn"]

def create_ml_pipeline(pipeline_name, s3_feature_store_uri, region=None):
    resolved_region = region or os.environ.get("AWS_REGION") or "ap-southeast-1"
    orchestrator = PipelineOrchestrator(resolved_region)
    return orchestrator.create_pipeline(pipeline_name, s3_feature_store_uri)