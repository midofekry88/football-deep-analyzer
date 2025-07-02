# streamlit_app.py

import streamlit as st
import pandas as pd
import requests
import tempfile
import os
import json
from fpdf import FPDF
from io import BytesIO


st.set_page_config(page_title="Jokey Football Chat", layout="wide")
st.title("🧠 Jokey Football Analysis")

# قراءة prompt من URL
query_params = st.query_params
prompt_from_url = query_params.get("prompt", [""])[0]

# تحميل ملف Excel
uploaded_file = st.file_uploader("📤 Upload Excel or CSV", type=["xlsx", "csv"])

# قراءة البرومبت من ملف خارجي
try:
    with open("prompt.txt", "r", encoding="utf-8") as f:
        default_prompt = f.read()
except:
    default_prompt = "Analyze this match tactically"

user_prompt = st.text_area("📝 Prompt", default_prompt)

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
                    "messages": [{"role": "user", "content": full_prompt}],
                    "stream": True
                }

                # بدء الـ Streaming Response
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    stream=True
                )

                if response.status_code == 200:
                    st.success("✅ Streaming started...")
                    full_reply = ""
                    placeholder = st.empty()

                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode("utf-8")
                            if decoded_line.startswith("data: "):
                                try:
                                    data_json = json.loads(decoded_line[6:])
                                    delta = data_json["choices"][0]["delta"]
                                    content = delta.get("content", "")
                                    full_reply += content
                                    placeholder.markdown(full_reply + "▌")
                                except:
                                    pass

                    placeholder.markdown(full_reply)


                    # توليد PDF من التحليل

                    # إعداد خط يدعم العربية والرموز (DejaVuSans)
                    import urllib.request
                    font_path = os.path.join(tempfile.gettempdir(), "DejaVuSans.ttf")
                    if not os.path.exists(font_path):
                        url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
                        urllib.request.urlretrieve(url, font_path)

                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=15)
                    pdf.add_font("DejaVu", '', font_path, uni=True)
                    pdf.set_font("DejaVu", size=12)
                    for line in full_reply.split('\n'):
                        pdf.multi_cell(0, 10, line)

                    pdf_buffer = BytesIO()
                    pdf.output(pdf_buffer)
                    pdf_buffer.seek(0)

                    # زر تحميل PDF
                    st.download_button(
                    label="📥 Download Analysis as PDF",
                    data=pdf_buffer,
                    file_name=uploaded_file.name.rsplit('.', 1)[0] + "__analysis.pdf",
                    mime="application/pdf"
)
                else:
                    st.error(f"API Error: {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"Processing error: {str(e)}")
    else:
        st.warning("⚠️ Please upload a file and write a prompt.")