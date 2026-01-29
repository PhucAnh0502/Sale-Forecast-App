import streamlit as st
import os
from services.forecast_services import ForecastService
from services.model_services import ModelService

forecast_service = ForecastService()
model_service = ModelService()

st.set_page_config(page_title="Sales Forecast Application", layout="wide")

st.image("assets/MegazoneLogo.svg", width=300)
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
    
    approved_models = model_service.get_approved_models()
    s3_files = forecast_service.get_s3_inputs()

    col_sel1, col_sel2 = st.columns(2)
    
    with col_sel1:
        if approved_models:
            model_map = {f"Model {m['name']} ({m['creation_time']})": m['arn'] for m in approved_models}
            selected_model_label = st.selectbox("Select Approved Model", options=list(model_map.keys()))
            selected_model_arn = model_map[selected_model_label]
        else:
            st.warning("No approved models found.")
            selected_model_arn = None
        
    with col_sel2:
        if s3_files:
            selected_input_path = st.selectbox("Select Input Dataset (S3)", options=s3_files)
        else:
            st.warning("No processed files found on S3.")
            selected_input_path = None
    
    if st.button("Execute Forecast", type="primary", disabled=not (selected_model_arn and selected_input_path)):
        with st.spinner("Initializing SageMaker Batch Transform..."):
            res = forecast_service.batch_prediction(selected_model_arn, selected_input_path)
            if res:
                st.success("Job created successfully!")
                st.info(f"**Job Name:** {res['details']['TransformJobName']}")
                st.write(f"Results will be saved to: `{res['details']['OutputS3']}`")

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