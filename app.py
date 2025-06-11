import pandas as pd
import streamlit as st
import plotly.express as px
from pymongo import MongoClient
import duckdb
import os

# ✅ ตั้งค่า layout และไอคอน
st.set_page_config(
    page_title="Condo Rental Explorer",
    page_icon="🏠",
    layout="wide"
)

# ✅ เนื้อหาหลักของหน้าแรก
st.title("🏠 Welcome to Condo Rental Explorer")

st.markdown("""
Explore condo rental prices in Bangkok using interactive analytics and AI tools.

Use the menu on the left to navigate to:

- 📊 Descriptive Analysis  
- 📈 Relationship & Price Prediction  
- 🗺 Geospatial Analysis  
- 🤖 Advanced Search & Comparison  
""")

# ✅ ภาพประกอบ (ใส่ลิงก์หรือ path ได้)
st.image("https://cdn.pixabay.com/photo/2020/01/15/07/27/condominium-4769185_1280.jpg", use_container_width=True)

st.caption("Built with ❤️ using Streamlit, Plotly, and DuckDB")

def create_duckdb_from_csv():
    if not os.path.exists("condo.duckdb"):
        df = pd.read_csv("data_cleaned.csv")
        con = duckdb.connect("condo.duckdb")
        con.execute("DROP TABLE IF EXISTS condo")
        con.execute("CREATE TABLE condo AS SELECT * FROM df")
        con.close()
        print("DuckDB database created from CSV")
    else:
        print("DuckDB database already exists")
