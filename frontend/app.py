import streamlit as st
from services import ForecastService, ModelService, S3Service
from views import render_data_tab, render_training_tab, render_inference_tab, render_admin_tab

st.set_page_config(page_title="Sales Forecast", layout="wide")
forecast_service = ForecastService()
model_service = ModelService()
s3_service = S3Service()

st.image("assets/MegazoneLogo.svg", width=250)
st.title("Sales Forecast Dashboard")

tabs = st.tabs(["Data Ingestion", "Model Training", "Inference", "Model Admin"])

with tabs[0]: render_data_tab(forecast_service, s3_service)
with tabs[1]: render_training_tab(forecast_service, model_service)
with tabs[2]: render_inference_tab(forecast_service, model_service, s3_service)
with tabs[3]: render_admin_tab(model_service)