import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from pymongo import MongoClient

# --------------------------
# 🗺️ Bangkok Condo Map & Price Classification
# --------------------------
st.set_page_config(page_title="Condo Map", page_icon="🏙️", layout="wide")
st.title("🏙️ Bangkok Condo Map & Price Classification")

# --------------------------
# 🔄 Load Data from MongoDB
# --------------------------
@st.cache_data
def load_data():
    try:
        mongo_uri = st.secrets["MONGO_URI"]
        client = MongoClient(mongo_uri)
        db = client["data_cleaned"]  # ✅ Database name
        collection = db["data_cleaned"]  # ✅ Collection name

        data = list(collection.find({}, {"_id": 0}))
        df = pd.DataFrame(data)

        df['rent_cd_price'] = pd.to_numeric(df['rent_cd_price'], errors='coerce')
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df.dropna(subset=['latitude', 'longitude'], inplace=True)
        df = df[df['rent_cd_price'] <= 1000000]
        df['rate_type'] = df['rent_cd_price'].apply(lambda x: 0 if x < 10000 else (1 if x < 20000 else 2))
        return df
    except Exception as e:
        st.error("❌ MongoDB connection failed:")
        st.exception(e)
        return pd.DataFrame()  # return empty for safety

df = load_data()
if df.empty:
    st.stop()

# --------------------------
# Classification Map
# --------------------------
st.markdown("### 🗺️ Condo Classification Map by Rental Price")
st.markdown("""
🟧 **Low**: < 10,000 THB  
🟩 **Medium**: 10,000–19,999 THB  
🟪 **High**: ≥ 20,000 THB  
""")

rate_label_map = {0: "Low", 1: "Medium", 2: "High"}
df['rate_label'] = df['rate_type'].map(rate_label_map)

selected_class = st.multiselect(
    "Filter by Price Class",
    options=["Low", "Medium", "High"],
    default=["Low", "Medium", "High"]
)

df = df[df['rate_label'].isin(selected_class)].copy()

icon_url_map = {
    "Low": "https://cdn-icons-png.flaticon.com/128/5111/5111178.png",
    "Medium": "https://cdn-icons-png.flaticon.com/128/8838/8838901.png",
    "High": "https://cdn-icons-png.flaticon.com/128/16740/16740174.png",
}

df['icon_data'] = df['rate_label'].apply(lambda x: {
    "url": icon_url_map[x], "width": 128, "height": 128, "anchorY": 128
})

df['latitude'] += np.random.uniform(-0.0001, 0.0001, size=len(df))
df['longitude'] += np.random.uniform(-0.0001, 0.0001, size=len(df))

icon_layer = pdk.Layer(
    "IconLayer",
    data=df,
    get_icon="icon_data",
    get_position='[longitude, latitude]',
    get_size=4,
    size_scale=15,
    pickable=True,
)

view_state = pdk.ViewState(latitude=13.75, longitude=100.52, zoom=11)
st.pydeck_chart(pdk.Deck(
    layers=[icon_layer],
    initial_view_state=view_state,
    tooltip={"text": "🏢 {new_condo_name}\n💰 Price: {rent_cd_price} THB\n🎯 Class: {rate_label}"}
))

# --------------------------
# Filter Section
# --------------------------
st.markdown("---")
st.markdown("### 🔍 Filter and Explore Condos")

grouped = df.groupby(['new_condo_name', 'latitude', 'longitude'], as_index=False).agg({
    'rent_cd_price': ['min', 'max', 'mean'],
    'rent_cd_bed': 'max',
    'rent_cd_bath': 'max',
    'rent_cd_floorarea': ['min', 'max', 'mean'],
    'star': 'mean',
    'near_rail_meter': 'min'
})
grouped.columns = [
    'Condo Name', 'Latitude', 'Longitude', 'Min Price', 'Max Price', 'Avg Price',
    'Bedrooms', 'Bathrooms', 'Min Area', 'Max Area', 'Avg Area', 'Avg Rating', 'MRT Distance'
]
grouped = grouped.round(1)

bedroom = st.selectbox("Number of Bedrooms", sorted(grouped['Bedrooms'].dropna().unique()))
bathroom = st.selectbox("Number of Bathrooms", sorted(grouped['Bathrooms'].dropna().unique()))
min_price = st.number_input("Minimum Price", min_value=0, value=10000)
max_price = st.number_input("Maximum Price", value=30000)
min_area = st.number_input("Minimum Area", value=25)
max_area = st.number_input("Maximum Area", value=80)
rating = st.slider("Minimum Rating", 3.5, 5.0, 4.0, step=0.1)

filtered = grouped[
    (grouped['Bedrooms'] == bedroom) &
    (grouped['Bathrooms'] == bathroom) &
    (grouped['Avg Price'] >= min_price) &
    (grouped['Avg Price'] <= max_price) &
    (grouped['Avg Rating'] >= rating) &
    (grouped['Avg Area'] >= min_area) &
    (grouped['Avg Area'] <= max_area)
].copy()

filtered['tooltip'] = (
    "🏢 " + filtered['Condo Name'] + "<br>" +
    "💰 Avg Price: " + filtered['Avg Price'].astype(int).astype(str) + " THB<br>" +
    "🛏️ Bed: " + filtered['Bedrooms'].astype(str) + ", 🛁 Bath: " + filtered['Bathrooms'].astype(str) + "<br>" +
    "⭐ Rating: " + filtered['Avg Rating'].astype(str) + "<br>" +
    "🚆 MRT Distance: " + filtered['MRT Distance'].fillna(-1).apply(lambda x: f"{int(x)} m" if x >= 0 else "N/A")
)

filtered['icon_data'] = [{
    "url": "https://cdn-icons-png.flaticon.com/512/684/684908.png",
    "width": 128,
    "height": 128,
    "anchorY": 128
}] * len(filtered)

layer = pdk.Layer(
    "IconLayer",
    data=filtered,
    get_position='[Longitude, Latitude]',
    get_icon='icon_data',
    get_size=4,
    size_scale=15,
    pickable=True,
    auto_highlight=True
)

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"html": "{tooltip}", "style": {"backgroundColor": "white", "color": "black"}}
))

if st.checkbox("Show condo data table"):
    st.dataframe(
        filtered[[
            'Condo Name', 'Avg Price', 'Min Price', 'Max Price',
            'Bedrooms', 'Bathrooms', 'Min Area', 'Max Area', 'Avg Rating', 'MRT Distance'
        ]].rename(columns={
            'Avg Price': 'Avg Price (THB)',
            'Min Price': 'Min Price (THB)',
            'Max Price': 'Max Price (THB)',
            'Avg Rating': 'Rating',
            'MRT Distance': 'Distance to MRT/BTS'
        }),
        use_container_width=True
    )

# --------------------------
# Show listings of selected condo
# --------------------------
st.markdown("---")
selected_condo = st.selectbox("📌 Select a Condo to View Listings", df['new_condo_name'].dropna().unique())
condo_details = df[df['new_condo_name'] == selected_condo]
st.dataframe(
    condo_details[[
        'new_condo_name', 'rent_cd_price', 'rent_cd_bed', 'rent_cd_bath',
        'rent_cd_floorarea', 'star', 'rent_cd_agent', 'rent_cd_tel'
    ]].rename(columns={
        'new_condo_name': 'Condo Name',
        'rent_cd_price': 'Price (THB)',
        'rent_cd_bed': 'Bedrooms',
        'rent_cd_bath': 'Bathrooms',
        'rent_cd_floorarea': 'Area',
        'star': 'Rating',
        'rent_cd_agent': 'Agent',
        'rent_cd_tel': 'Tel'
    }),
    use_container_width=True
)
