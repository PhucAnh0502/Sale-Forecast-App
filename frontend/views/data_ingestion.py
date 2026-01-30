import streamlit as st
import pandas as pd
import io
import base64
import binascii

@st.dialog("File Content", width="large")
def show_file_content_modal(bucket_type, file_key, s3_service):
    with st.spinner("Getting content..."):
        content_res = s3_service.get_file_content(bucket_type, file_key)
        if not content_res:
            st.error("Failed to retrieve file content.")
            return
        
        if isinstance(content_res, dict):
            content = content_res.get("content")
        else:
            content = content_res

        if content is None:
            st.error("File content is empty.")
            return

        is_base64 = False
        file_bytes = b""
        if isinstance(content, str):
            try:
                file_bytes = base64.b64decode(content, validate=True)
                is_base64 = True
            except (binascii.Error, ValueError):
                file_bytes = content.encode("utf-8")
        elif isinstance(content, bytes):
            file_bytes = content
        else:
            file_bytes = str(content).encode("utf-8")

        file_ext = file_key.split('.')[-1].lower()

        try:
            if file_ext == 'pdf':
                if is_base64 and isinstance(content, str):
                    pdf_display = f'<iframe src="data:application/pdf;base64,{content}" width="100%" height="700" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                else:
                    st.code(file_bytes.decode("utf-8", errors="replace"))

            elif file_ext in ['xlsx', 'xls']:
                if not is_base64:
                    st.code(file_bytes.decode("utf-8", errors="replace"))
                else:
                    try:
                        df = pd.read_excel(io.BytesIO(file_bytes))
                        st.dataframe(df, use_container_width=True)
                    except Exception:
                        st.code(file_bytes.decode("utf-8", errors="replace"))

            elif file_ext == 'csv':
                if is_base64:
                    df = pd.read_csv(io.BytesIO(file_bytes))
                else:
                    df = pd.read_csv(io.StringIO(file_bytes.decode("utf-8", errors="replace")))
                st.dataframe(df, use_container_width=True)

            elif file_ext == 'parquet':
                if is_base64:
                    df = pd.read_parquet(io.BytesIO(file_bytes))
                    st.dataframe(df, use_container_width=True)
                else:
                    st.code(file_bytes.decode("utf-8", errors="replace"))

            else:
                st.code(file_bytes.decode('utf-8'))
        except Exception as e:
            st.error(f"File show error: {e}")
            st.download_button("Download file", data=file_bytes, file_name=file_key)

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
        event = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun" 
        )

        if event.selection.rows:
            selected_idx = event.selection.rows[0]
            file_name = df.iloc[selected_idx]['filename']
            show_file_content_modal(bucket_option, file_name, s3_service)
    else:
        st.info("No files found in this bucket.")