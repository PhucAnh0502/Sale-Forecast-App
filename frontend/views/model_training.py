import streamlit as st
import json
import pandas as pd
from utils import to_float

def render_training_tab(forecast_service, model_service):
    st.header("ML Pipeline Orchestration")
    
    if st.button("Run Training Pipeline", type="primary"):
        res = forecast_service.trigger_train() 
        if not res:
            st.error("Failed to trigger pipeline.")
            return

        execution_arn = res.get('execution_arn')
        st.info(f"Pipeline Execution Started")
        
        with st.status("Running Pipeline...", expanded=True) as status:
            response = forecast_service.stream_train_progress(execution_arn)
            if not response:
                st.error("Failed to connect to stream.")
                return

            step_label = st.empty()
            completed_steps = set() 
            
            for line in response.iter_lines():
                if not line: continue
                data = json.loads(line.decode('utf-8')[6:])
                steps = data.get('steps', [])
                overall = data.get('overall_status')

                for step in steps:
                    name, s_status = step['step_name'], step['status']
                    if s_status == 'Executing':
                        step_label.write(f"Running: **{name}**")
                    elif s_status == 'Succeeded' and name not in completed_steps:
                        st.write(f"Done: **{name}**")
                        completed_steps.add(name)
                
                if overall == 'Succeeded':
                    status.update(label="Pipeline completed!", state="complete", expanded=False)
                    _display_metrics(model_service)
                    break
                elif overall == 'Failed':
                    status.update(label="Pipeline failed!", state="error")
                    break

def _display_metrics(model_service):
    pending_res = model_service.get_pending_models()
    pending_list = pending_res.get("pending_models", []) if pending_res else []
    if not pending_list: return

    metrics_data = model_service.get_metrics(pending_list[0]['arn'])
    if metrics_data:
        st.divider()
        st.subheader("Model Evaluation Metrics")
        reg = metrics_data.get('regression_metrics', {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("MSE", f"{to_float(reg.get('mse', {}).get('value')):.4f}")
        c2.metric("MAE", f"{to_float(reg.get('mae', {}).get('value')):.4f}")
        c3.metric("R²", f"{to_float(reg.get('r2', {}).get('value')):.4f}")
        c4.metric("MAPE", f"{to_float(reg.get('mape', {}).get('value')):.2f}%")

        importance = metrics_data.get('feature_importance', {})
        if importance:
            st.write("**Feature Importance:**")
            fi_df = pd.DataFrame(list(importance.items()), columns=['Feature', 'Weight']).sort_values(by='Weight')
            st.bar_chart(fi_df.set_index('Feature'))