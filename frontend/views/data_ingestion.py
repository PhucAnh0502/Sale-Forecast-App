import streamlit as st
import pandas as pd

def render_data_tab(forecast_service, s3_service):
    st.header("Data Upload & Processing")
    uploaded_files = st.file_uploader(
        "Drag and drop data files (PDF, CSV, XLSX)", 
        type=["pdf", "csv", "xlsx"], 
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("Start Ingestion", type="primary"):
        with st.spinner(f"Uploading {len(uploaded_files)} files to S3 Raw..."):
            res = forecast_service.upload_data(uploaded_files)
            if res:
                st.success(res["message"])
                for item in res["data"]:
                    st.write(f"{item['filename']} -> `{item['s3_uri']}`")
            else:
                st.error("Failed to upload files.")

    st.divider()

    col_h, col_btn = st.columns([0.85, 0.15])
    with col_h:
        st.header("S3 Data Explorer")

    bucket_options = {
        "Raw Data": "raw",
        "Processed Data": "processed",
        "Feature Store": "feature-store"
    }
    
    bucket_display = st.selectbox("Choose your bucket:", list(bucket_options.keys()))
    bucket_option = bucket_options[bucket_display]

    files = s3_service.get_bucket_files(bucket_option)
    if files:
        df = pd.DataFrame(files)
        st.table(df) 
    else:
        st.info("No files found or the bucket is empty.")