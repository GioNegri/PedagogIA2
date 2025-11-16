import google.generativeai as genai
import streamlit as st

def configurar_api():
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
