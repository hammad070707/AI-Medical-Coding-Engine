import streamlit as st
import asyncio
import os
import base64
from main import run_coding_pipeline
from datetime import datetime

st.set_page_config(page_title="MediCode SaaS", layout="wide")
st.markdown("""
    <style>
    .stAlert { border-radius: 10px; }
    .report-box { background: #f0f2f6; padding: 20px; border-radius: 15px; border: 1px solid #d1d3d4; }
    .bahi-bot { background: #e1f5fe; padding: 15px; border-radius: 15px; border-left: 5px solid #0288d1; }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 MediCode AI - Enterprise RCM Dashboard")
with st.sidebar:
    st.header("1. Patient Details")
    p_age = st.number_input("Age", 0, 100, 32)
    p_gender = st.selectbox("Gender", ["F", "M"])
    st.header("2. Upload Note")
    uploaded_file = st.file_uploader("Drop PDF, Image or Text", type=['pdf', 'jpg', 'png', 'txt'])

if uploaded_file:
    file_path = f"data/notes/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    with st.spinner("🤖 , AI Thinking..........."):
        result = asyncio.run(run_coding_pipeline(file_path, p_age, p_gender))
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 Original Input")
        if uploaded_file.type == "application/pdf":
            with open(file_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            st.markdown(f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf">', unsafe_allow_html=True)
        elif uploaded_file.type in ["image/jpeg", "image/png"]:
            st.image(file_path, use_column_width=True)
        else:
            with open(file_path, "r") as f:
                st.text_area("Raw Text", f.read(), height=400)

    with col2:
        st.subheader("🚩 Phase 1: AI Audit")
        p1 = result['phase1']
        st.metric("Initial Score", f"{p1['score']}/100", delta=None)
        st.write(f"**Codes:** {p1['icd']} | **CPT:** {p1['cpt']}")

        if result['phase2_suggestions']:
            st.subheader("💡 AI Suggestions")
            for s in result['phase2_suggestions']:
                st.warning(f"**{s['missing_element']}**: {s['suggested_text']}")

        st.subheader("✅ Final Submission Note")
        final_note = result['phase3_final'].get('full_note', "Error generating note")
        st.text_area("Audit-Proof Note", final_note, height=350)
        
        st.download_button("📥 Download Final PDF/Text", final_note, file_name="Approved_Claim.txt")
        if result['phase2_suggestions']:
            st.markdown("<div class='bahi-bot'><b>🤖 MediCode AI Bot:</b><br>To ensure your claim is 100% approved, please review and attach the required Addendum below. This will provide the necessary supporting details to finalize your request..</div>", unsafe_allow_html=True)
        if result.get('phase3_final'):
            st.markdown("---")
            st.subheader("✅ Phase 3: FINAL APPROVED REPORT")
            p3 = result['phase3_final']
            st.success(f"🎉 FINAL COMPLIANCE SCORE: {p3['score']}/100")
            with st.container():
            
                st.markdown("#### 🚀 SUBMISSION READY DATA")
                st.info(f"**Final ICD-10 Code(s):**  \n{p3['icd']}")
                st.warning(f"**Final CPT Procedure Code(s):**  \n{', '.join(p3['cpt'])}")
                mod_display = ", ".join(p3['modifiers']) if p3['modifiers'] else "None"
                st.success(f"**Final Modifier(s):**  \n{mod_display}")
            st.download_button(
                label="📥 Download Submission Ready Report",
                data=p3['full_note'],
                file_name="Approved_Claim.txt",
                mime="text/plain"
            )
            st.balloons()

        st.subheader("📑 Submission Note")
        st.text_area("Optimized Content", result['phase3_final'].get('full_note', "Processing..."), height=300)

else:
    st.warning("👈 Upload your note to get started!")
    