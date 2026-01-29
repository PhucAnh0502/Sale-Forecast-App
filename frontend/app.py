import streamlit as st
import pandas as pd
import os
from services.forecast_services import ForecastService
from dotenv import load_dotenv

load_dotenv()
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "assets", "style.css")
forecast_service = ForecastService()

st.set_page_config(
    page_title="Sale Forecast App",
    layout="wide",
)

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file '{file_name}' not found.")

local_css(css_path)

st.title("Sale Forecast Application")
st.markdown("---")

col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.header("Upload File")
    uploaded_file = st.file_uploader("Upload your data here", type=["csv", "xlsx", "pdf"])
    if uploaded_file and st.button("Upload File"):
        with st.spinner("Uploading file..."):
            result = forecast_service.upload_data(uploaded_file)
            if result:
                st.success(f"S3 URI: {result.get('s3_uri', '')}")
            else:
                st.error("File upload failed.")

with col_right:
    st.header("Model Operations")
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("Train Model"):
            with st.spinner("Training model..."):
                result = forecast_service.trigger_train()
                if result:
                    st.success(f"Started: {result.get('execution_arn', '')}")
                else:
                    st.error("Model training failed.")
    with col_btn2:
        if st.button("Retrain Model"):
            with st.spinner("Retraining model..."):
                result = forecast_service.trigger_train()
                if result:
                    st.success(f"Started: {result.get('execution_arn', '')}")
                else:
                    st.error("Model retraining failed.")
    with col_btn3:
        model_arn = st.text_input("Model ARN", "")
        input_path = st.text_input("Input S3 Path", "")
        if st.button("Predict"):
            with st.spinner("Starting batch prediction..."):
                result = forecast_service.batch_prediction(model_arn, input_path)
                if result:
                    st.json(result.get("details", {}))
                else:
                    st.error("Batch prediction failed.")

st.markdown("---")