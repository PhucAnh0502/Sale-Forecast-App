import streamlit as st
import os
from services.forecast_services import ForecastService
from services.model_services import ModelService

forecast_service = ForecastService()
model_service = ModelService()

st.set_page_config(page_title="Sales Forecast Application", layout="wide")

with st.sidebar:
    st.image("assets/MegazoneLogo.svg", width=200)
    st.title("Sales Forecast App")

st.title("Sales Forecast Application Dashboard")

tab_data, tab_train, tab_predict, tab_admin = st.tabs([
    "Data Ingestion", "Model Training", "Inference", "Model Admin"
])

with tab_data:
    st.header("Data Upload & Processing")
    uploaded_files = st.file_uploader(
        "Drag and drop data files (PDF, CSV, XLSX)", 
        type=["pdf", "csv", "xlsx"], 
        accept_multiple_files=True
    )
    if uploaded_files and st.button("Start Ingestion", type="primary"):
        with st.spinner(f"Đang tải {len(uploaded_files)} file lên S3 Raw..."):
            res = forecast_service.upload_data(uploaded_files)
            if res:
                st.success(res["message"])
                for item in res["data"]:
                    st.write(f"{item['filename']} -> `{item['s3_uri']}`")

with tab_train:
    st.header("ML Pipeline Orchestration")
    st.info("Press the button below to trigger the Pipeline")
    if st.button("Run Training Pipeline"):
        res = forecast_service.trigger_train()
        st.warning(f"Pipeline Execution ARN: {res['execution_arn']}")

with tab_predict:
    st.header("Batch Prediction")
    
    col_sel1, col_sel2 = st.columns(2)
    
    with col_sel1:
        model_options = {
            "Model 1": "arn:aws:sagemaker:ap-southeast-1:123456789012:model/sales-v1",
            "Model 2": "arn:aws:sagemaker:ap-southeast-1:123456789012:model/sales-v1-1"
        }
        selected_model_name = st.selectbox("Select Model", options=list(model_options.keys()))
        selected_model_arn = model_options[selected_model_name]
        
    with col_sel2:
        input_options = [
            "s3://processed-data-bucket/data_january.parquet",
            "s3://processed-data-bucket/data_february.parquet"
        ]
        selected_input_path = st.selectbox("Select Input Data (S3)", options=input_options)
    
    if st.button("Execute Forecast", type="primary"):
        with st.spinner("Sending forecast request to the system..."):
            res = forecast_service.batch_prediction(selected_model_arn, selected_input_path)
            
            if res:
                st.success("Forecast request has been accepted!")
                st.info(f"**Job Name:** {res['details']['TransformJobName']}")
                st.write(f"Results will be saved at: `{res['details']['OutputS3']}`")
                st.toast("Batch Transform Job has been started.")
            else:
                st.error("Error: Unable to connect to Predict API or invalid parameters.")

with tab_admin:
    st.header("Model Governance")
    pending = model_service.get_pending_models()
    
    if not pending:
        st.write("No models pending approval.")
    else:
        for m in pending:
            with st.expander(f"Model Version {m['version']} - {m['creation_time']}"):
                st.write(f"ARN: `{m['arn']}`")
                cmt = st.text_area("Review Comment", key=f"cmt_{m['version']}")
                btn_c1, btn_c2 = st.columns(5)
                with btn_c1:
                    if st.button("Approve", key=f"app_{m['version']}", type="primary"):
                        model_service.approve_model(m['arn'], cmt)
                        st.rerun()
                with btn_c2:
                    if st.button("Reject", key=f"rej_{m['version']}", type="secondary"):
                        model_service.reject_model(m['arn'], cmt)
                        st.rerun()