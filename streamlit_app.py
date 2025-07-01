# streamlit_app.py

import streamlit as st
import pandas as pd
import requests
import tempfile
import os

st.set_page_config(page_title="Deep Football Chat", layout="wide")
st.title("🧠 DeepSeek Football Analysis")

# قراءة prompt من URL
query_params = st.experimental_get_query_params()
prompt_from_url = query_params.get("prompt", [""])[0]

# تحميل ملف Excel
uploaded_file = st.file_uploader("📤 Upload Excel or CSV", type=["xlsx", "csv"])

# إدخال البرومبت يدويًا أو من URL
user_prompt = st.text_area("📝 Prompt", prompt_from_url or "Analyze this match tactically")

if st.button("🔍 Analyze"):
    if uploaded_file and user_prompt.strip():
        with st.spinner("Thinking deeply..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    file_path = tmp.name

                df = pd.read_excel(file_path) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(file_path)
                os.unlink(file_path)

                st.subheader("📊 Uploaded Data")
                st.dataframe(df)

                full_prompt = f"""Analyze the following football match data:

{df.to_string(index=False)}

User Request:
{user_prompt}
"""

                headers = {
                    "Authorization": f"Bearer {st.secrets['api_key']}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://yourapp.streamlit.app",
                    "X-Title": "Deep Football Chat"
                }

                payload = {
                    "model": "deepseek/deepseek-r1:free",
                    "messages": [{"role": "user", "content": full_prompt}]
                }

                response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                         headers=headers, json=payload)

                if response.status_code == 200:
                    reply = response.json()['choices'][0]['message']['content']
                    st.success("✅ Analysis Completed")
                    st.markdown(reply)
                else:
                    st.error(f"API Error: {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"Processing error: {str(e)}")
    else:
        st.warning("⚠️ Please upload a file and write a prompt.")