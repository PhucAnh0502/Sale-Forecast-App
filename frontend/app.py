import streamlit as st
import requests
import pandas as pd
import os

current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "assets", "style.css")

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
    if uploaded_file:
        st.success("File uploaded successfully!")
        if st.button("Load to S3 Raw Data Bucket"):
            st.toast("Uploading to S3...")

with col_right:
    st.header("Model Operations")
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("Train Model"):
            st.toast("Training model...")
    with col_btn2:
        if st.button("Retrain Model"):
            st.toast("Retraining model...")
    with col_btn3:
        if st.button("Predict Sales"):
            st.toast("Predicting sales...")

st.markdown("---")