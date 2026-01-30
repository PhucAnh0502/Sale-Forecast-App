import streamlit as st
import json
import pandas as pd

def render_inference_tab(forecast_service, model_service, s3_service):
    st.header("Batch Prediction")
    
    models_res = model_service.get_approved_models()
    s3_res = s3_service.get_s3_inputs()

    approved_models = models_res.get("approved_models", []) if models_res else []
    s3_files = s3_res.get("s3_inputs", []) if isinstance(s3_res, dict) else s3_res

    col1, col2 = st.columns(2)
    with col1:
        selected_model_arn = None
        if approved_models:
            model_map = {f"{m['name']} ({m['creation_time']})": m['arn'] for m in approved_models}
            selected_label = st.selectbox("Select Model", options=list(model_map.keys()))
            selected_model_arn = model_map[selected_label]
    
    with col2:
        selected_input = st.selectbox("Select Input Data", options=s3_files) if s3_files else None

    if st.button("Execute Forecast", type="primary", disabled=not (selected_model_arn and selected_input)):
        res = forecast_service.batch_prediction(selected_model_arn, selected_input)
        if res:
            _run_prediction_stream(forecast_service, res['details'])

def _run_prediction_stream(forecast_service, details):
    job_name = details.get('TransformJobName') or details.get('job_name')
    if not job_name:
        st.error("Prediction job name not found in response.")
        return
    st.success(f"Job Created: {job_name}")
    
    with st.status("Running Prediction...", expanded=True) as status:
        response = forecast_service.stream_prediction_progress(job_name)
        progress_bar = st.progress(0)
        msg_box = st.empty()
        
        for line in response.iter_lines():
            if not line:
                continue
            try:
                decoded = line.decode('utf-8')
            except UnicodeDecodeError:
                continue
            if not decoded.startswith("data:"):
                continue
            try:
                data = json.loads(decoded[5:].strip())
            except json.JSONDecodeError:
                continue
            prog = data.get('progress_percentage', 0)
            progress_bar.progress(prog / 100)
            msg_box.write(f"**{data.get('status')}**: {data.get('message')}")
            
            if prog >= 100:
                status.update(label="Completed!", state="complete")
                _show_results(forecast_service, job_name)
                break

def _show_results(forecast_service, job_name):
    results = forecast_service.get_prediction_results(job_name)
    if results:
        st.subheader("Results")
        df = pd.DataFrame(results['predictions'])
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), f"{job_name}.csv", "text/csv")