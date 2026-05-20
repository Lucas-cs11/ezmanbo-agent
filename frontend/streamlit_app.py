import streamlit as st
import requests

API_URL = st.secrets.get("api_url", "http://localhost:8000")

st.title("eZ-PLM Component Selection Demo")
user_input = st.text_area("Requirement", value="我需要一个 12V 转 5V、3A 的车规级降压方案，工作温度 -40°C 到 125°C，优先考虑国产替代。", height=120)

if st.button("Analyze"):
    try:
        resp = requests.post(f"{API_URL}/analyze", json={"user_input": user_input}, timeout=10)
        data = resp.json()
        st.subheader("SelectionReport (IR)")
        st.json(data)
    except Exception as e:
        st.error(f"Error calling backend: {e}")

