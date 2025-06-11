import pandas as pd
import streamlit as st
#from sqlalchemy import create_engine
from pymongo import MongoClient
import duckdb

# === Set page ===
st.set_page_config(
    page_title=" Home",
    page_icon="🏠",
    layout="wide",
    #initial_sidebar_state="collapsed"
)

# === Database Connections ===
#engine = create_engine("mysql+mysqlconnector://root:admin@localhost:3306/dads5001db")
#client = MongoClient("mongodb://root:admin@localhost:27017/?authSource=admin")

# === Load data from DuckDB ===
def load_data():
    con = duckdb.connect("condo.duckdb")
    df = con.execute("SELECT * FROM condo").df()
    con.close()
    return df

# === Helper function ===
def rating_to_stars(rating, max_stars=5):
    if pd.isna(rating):
        return "N/A"
    full_stars = "⭐" * int(rating)
    empty_stars = "☆" * (max_stars - int(rating))
    return full_stars + empty_stars

# === Page content ===
st.title("🏠 Smart Rent BKK")
st.markdown("""
Explore Bangkok's condo rental market! This dashboard shows price distributions, factors affecting rent, predictions, and AI-powered recommendations to help you make the smartest decision.
""")

st.image("https://raw.githubusercontent.com/ppitchaporn/DADS5001-Condo/a785a69fe796a14d3023d993a8c89289c4bd067a/Condo_image.jpg")

st.header("🏢 All Condominium List")
st.markdown("(Loaded from DuckDB)")

# Load data
df = load_data()
df["Rating"] = df["star"].apply(rating_to_stars)

# === Display Table ===
st.dataframe(
    df,
    column_config={
        "Rating": st.column_config.Column("Rating", help="คะแนนรีวิว", width="small"),
        "star": None
    },
    column_order=[
        "Condo Name", "Rating", "Address", "Rental Price (Baht)", "#Bed", "#Bath",
        "Rail Station", "Distance from rails (Meters)", "Time to rails (Minutes)"
    ],
    hide_index=True
)

# === MongoDB connection info ===
#st.markdown("## 🔗 Connect to MongoDB")
#db = client.dads5001db
#collections = db.list_collection_names()
#st.write(collections)
