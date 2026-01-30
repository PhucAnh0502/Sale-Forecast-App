import streamlit as st
from services import ForecastService, ModelService, S3Service
import json

def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

forecast_service = ForecastService()
model_service = ModelService()
s3_service = S3Service()

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
        with st.spinner(f"Uploading {len(uploaded_files)} files to S3 Raw..."):
            res = forecast_service.upload_data(uploaded_files)
            if res:
                st.success(res["message"])
                for item in res["data"]:
                    st.write(f"{item['filename']} -> `{item['s3_uri']}`")
            else:
                st.error("Failed to upload files. Please check backend connection.")
    
    st.header("S3 Data Explorer")
    
    bucket_options = {
        "Raw Data": "raw",
        "Processed Data": "processed",
        "Feature Store": "feature-store"
    }
    
    bucket_display = st.selectbox(
        "Choose your bucket:",
        list(bucket_options.keys()),
        key="bucket_selector"
    )
    
    bucket_option = bucket_options[bucket_display]

    files = s3_service.get_bucket_files(bucket_option)
    if files:
        import pandas as pd
        df = pd.DataFrame(files)
        st.table(df) 
    else:
        st.info("No files found or the bucket is empty.")

with tab_train:
    st.header("ML Pipeline Orchestration")
    
    if st.button("Run Training Pipeline"):
        res = forecast_service.trigger_train() 
        
        if not res:
            st.error("Failed to trigger training pipeline. Please check backend connection.")
        else:
            execution_arn = res.get('execution_arn')
            
            if execution_arn:
                st.info(f"Pipeline Execution Started")
                
                with st.status("Running Pipeline...", expanded=True) as status:
                    response = forecast_service.stream_train_progress(execution_arn)
                    
                    if response is None:
                        st.error("Failed to connect to pipeline stream.")
                    else:
                        step_label = st.empty()
                        completed_steps = set() 
                        
                        for line in response.iter_lines():
                            if line:
                                decoded_line = line.decode('utf-8')
                                if decoded_line.startswith("data: "):
                                    data = json.loads(decoded_line[6:])
                                    steps = data.get('steps', [])
                                    overall = data.get('overall_status')

                                    for step in steps:
                                        name = step['step_name']
                                        s_status = step['status']
                                        
                                        if s_status == 'Executing':
                                            step_label.write(f"Running: **{name}**")
                                        elif s_status == 'Succeeded' and name not in completed_steps:
                                            st.write(f"Done: **{name}**")
                                            completed_steps.add(name)
                                    
                                    if overall == 'Succeeded':
                                        status.update(label="Pipeline completed successfully!", state="complete", expanded=False)

                                        pending_res = model_service.get_pending_models()
                                        pending_list = pending_res.get("pending_models", []) if pending_res else []

                                        if pending_list:
                                            latest_model_arn = pending_list[0]['arn']
                                            metrics_data =  model_service.get_metrics(latest_model_arn)
                                        
                                        if metrics_data:
                                            st.divider()
                                            st.subheader("Model Evaluation Metrics")

                                            reg = metrics_data.get('regression_metrics', {})
                                            col1, col2, col3, col4 = st.columns(4)
                                            col1.metric("MSE", f"{_to_float(reg.get('mse', {}).get('value', 0)):.4f}")
                                            col2.metric("MAE", f"{_to_float(reg.get('mae', {}).get('value', 0)):.4f}")
                                            col3.metric("R²", f"{_to_float(reg.get('r2', {}).get('value', 0)):.4f}")
                                            col4.metric("MAPE", f"{_to_float(reg.get('mape', {}).get('value', 0)):.2f}%")

                                            importance = metrics_data.get('feature_importance', {})
                                            if importance:
                                                st.write("**Feature Importance:**")
                                                import pandas as pd
                                                fi_df = pd.DataFrame(list(importance.items()), columns=['Feature', 'Weight']).sort_values(by='Weight', ascending=True)
                                                st.bar_chart(fi_df.set_index('Feature')) 

                                        break
                                    elif overall == 'Failed':
                                        status.update(label="Pipeline failed!", state="error", expanded=True)
                                        break

with tab_predict:
    st.header("Batch Prediction")
    
    models_response = model_service.get_approved_models()
    s3_response = s3_service.get_s3_inputs()

    approved_models = models_response.get("approved_models", []) if models_response else []
    s3_files = s3_response.get("s3_inputs", []) if isinstance(s3_response, dict) else (s3_response if isinstance(s3_response, list) else [])

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
        res = forecast_service.batch_prediction(selected_model_arn, selected_input_path)
        if res:
            job_name = res['details']['TransformJobName']
            st.success("Job created successfully!")
            st.info(f"**Job Name:** {job_name}")
            st.write(f"Results will be saved to: `{res['details']['OutputS3']}`")
            
            with st.status("Running Prediction Job...", expanded=True) as status:
                response = forecast_service.stream_prediction_progress(job_name)
                
                if response:
                    progress_placeholder = st.empty()
                    message_placeholder = st.empty()
                    
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith("data: "):
                                data = json.loads(decoded_line[6:])
                                progress = data.get('progress_percentage', 0)
                                msg = data.get('message', '')
                                stage = data.get('status', '')
                                
                                progress_placeholder.progress(progress / 100)
                                message_placeholder.write(f"**{stage}**: {msg}")
                                
                                if progress >= 100:
                                    status.update(label="Prediction Completed!", state="complete", expanded=False)
                                    
                                    # Get prediction results
                                    results = forecast_service.get_prediction_results(job_name)
                                    if results:
                                        st.subheader("Prediction Results")
                                        
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Total Predictions", results['summary']['total_predictions'])
                                        with col2:
                                            st.metric("Avg Confidence", f"{results['summary']['avg_confidence']*100:.1f}%")
                                        with col3:
                                            st.metric("Completed At", results['summary']['completion_time'])

                                        import pandas as pd
                                        df = pd.DataFrame(results['predictions'])
                                        st.dataframe(df, use_container_width=True)

                                        csv = df.to_csv(index=False)
                                        st.download_button(
                                            label="Download Results (CSV)",
                                            data=csv,
                                            file_name=f"{job_name}_predictions.csv",
                                            mime="text/csv"
                                        )
                                    break
        else:
            st.error("Failed to create batch prediction job. Please check backend connection.")

with tab_admin:
    st.header("Model Governance")
    pending_response = model_service.get_pending_models()
    pending = pending_response.get("pending_models", []) if pending_response else []
    
    if not pending:
        st.write("No models pending approval.")
    else:
        for m in pending:
            with st.expander(f"Model Version {m['version']} - {m['creation_time']}"):
                st.write(f"ARN: `{m['arn']}`")
                if "metrics" in m and "regression_metrics" in m["metrics"]:
                    st.write("### Performance Metrics")
                    metrics = m["metrics"]["regression_metrics"]
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("MSE", f"{metrics.get('mse', {}).get('value', 0):.4f}")
                    c2.metric("MAE", f"{metrics.get('mae', {}).get('value', 0):.2f}")
                    c3.metric("R²", f"{metrics.get('r2', {}).get('value', 0):.4f}")
                    c4.metric("MAPE", f"{metrics.get('mape', {}).get('value', 0):.1f}%")
                else:
                    st.warning("No metrics available for this version.")
                st.divider()
                cmt = st.text_area("Review Comment", key=f"cmt_{m['version']}")
                btn_c1, btn_c2, empty_r = st.columns([1, 1, 6], gap="small")
                with btn_c1:
                    if st.button("Approve", key=f"app_{m['version']}", type="primary", use_container_width=True):
                        model_service.approve_model(m['arn'], cmt)
                        st.rerun()

                with btn_c2:
                    if st.button("Reject", key=f"rej_{m['version']}", type="secondary", use_container_width=True):
                        model_service.reject_model(m['arn'], cmt)
                        st.rerun()