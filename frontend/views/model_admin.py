import streamlit as st
from utils import to_float

def render_admin_tab(model_service):
    st.header("Model Governance")
    pending = model_service.get_pending_models().get("pending_models", [])
    
    if not pending:
        st.info("No models pending approval.")
        return

    for m in pending:
        with st.expander(f"Version {m['version']} - {m['creation_time']}"):
            if "metrics" in m:
                met = m["metrics"].get("regression_metrics", {})
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("MSE", f"{to_float(met.get('mse', {}).get('value')):.4f}")
                c2.metric("MAE", f"{to_float(met.get('mae', {}).get('value')):.2f}")
                c3.metric("R²", f"{to_float(met.get('r2', {}).get('value')):.4f}")
                c4.metric("MAPE", f"{to_float(met.get('mape', {}).get('value')):.1f}%")
            
            comment = st.text_area("Comments", key=f"cmt_{m['version']}")
            b1, b2, _ = st.columns([1, 1, 6])
            if b1.button("Approve", key=f"app_{m['version']}", type="primary"):
                model_service.approve_model(m['arn'], comment)
                st.rerun()
            if b2.button("Reject", key=f"rej_{m['version']}"):
                model_service.reject_model(m['arn'], comment)
                st.rerun()