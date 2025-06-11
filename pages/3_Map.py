import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from pymongo import MongoClient

# --------------------------
# 🗺️ Page 4 - Map & Decision Tree Classification
# --------------------------
def page4():
    st.title(" Bangkok Condo Map & Price Classification")

    # --------------------------
    # 🔄 Load Data from MongoDB
    # --------------------------
    @st.cache_data
    def load_data():

        mongo_uri = st.secrets["MONGO_URI"]
        client = MongoClient(mongo_uri)
    
        db = client["data_cleaned"]  # ✅ ชื่อจริงของ database
        collection = db["data_cleaned"]  # ✅ ชื่อ collection
    
        data = list(collection.find({}, {"_id": 0}))
        df = pd.DataFrame(data)

        df['rent_cd_price'] = pd.to_numeric(df['rent_cd_price'], errors='coerce')
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df.dropna(subset=['latitude', 'longitude'], inplace=True)
        df = df[df['rent_cd_price'] <= 1000000]
        df['rate_type'] = df['rent_cd_price'].apply(lambda x: 0 if x < 10000 else (1 if x < 20000 else 2))
        return df


    # --------------------------
    # Classification Map (based on rate_type)
    # --------------------------
    st.markdown("### \U0001F5FA️ Condo Classification Map by Rental Price")

    st.markdown(""" 
        🟧 **Low**: Rental price < 10,000 THB  
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
        tooltip={"text": "\U0001F3E2 {new_condo_name}\n\U0001F4B0 Price: {rent_cd_price} THB\n\U0001F3AF Class: {rate_label}"}
    ))

    st.markdown("---")
    st.markdown("### \U0001F50D Filter and Explore Condos")

    grouped = (
        df.groupby(['new_condo_name', 'latitude', 'longitude'], as_index=False)
        .agg({
            'rent_cd_price': ['min', 'max', 'mean'],
            'rent_cd_bed': 'max',
            'rent_cd_bath': 'max',
            'rent_cd_floorarea': ['min', 'max', 'mean'],
            'star': 'mean',
            'near_rail_meter': 'min'
        })
    )
    grouped.columns = ['Condo Name', 'Latitude', 'Longitude', 'Min Price', 'Max Price', 'Avg Price',
                       'Bedrooms', 'Bathrooms', 'Min Area', 'Max Area', 'Avg Area', 'Avg Rating', 'MRT Distance']

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
        "\U0001F3E2 " + filtered['Condo Name'] + "<br>" +
        "\U0001F4B0 Avg Price: " + filtered['Avg Price'].astype(int).astype(str) + " THB<br>" +
        "\U0001F6CF️ Bed: " + filtered['Bedrooms'].astype(str) + ", \U0001F6C1 Bath: " + filtered['Bathrooms'].astype(str) + "<br>" +
        "⭐ Rating: " + filtered['Avg Rating'].astype(str) + "<br>" +
        "\U0001F686 MRT Distance: " + filtered['MRT Distance'].fillna(-1).apply(lambda x: f"{int(x)} m" if x >= 0 else "N/A")
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

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"html": "{tooltip}", "style": {"backgroundColor": "white", "color": "black"}}
    )
    st.pydeck_chart(r)

    if st.checkbox("Show condo data table"):
        st.dataframe(
            filtered[[
                'Condo Name', 'Avg Price', 'Min Price', 'Max Price',
                'Bedrooms', 'Bathrooms', 'Min Area', 'Max Area', 'Avg Rating', 'MRT Distance']]
            .rename(columns={
                'Avg Price': 'Avg Price (THB)',
                'Min Price': 'Min Price (THB)',
                'Max Price': 'Max Price (THB)',
                'Avg Rating': 'Rating',
                'MRT Distance': 'Distance to MRT/BTS'
            }),
            use_container_width=True
        )

    st.markdown("---")
    selected_condo = st.selectbox("\U0001F4CC Select a Condo to View Listings", df['new_condo_name'].dropna().unique())
    condo_details = df[df['new_condo_name'] == selected_condo]
    st.dataframe(
        condo_details[[
            'new_condo_name', 'rent_cd_price', 'rent_cd_bed', 'rent_cd_bath',
            'rent_cd_floorarea', 'star', 'rent_cd_agent', 'rent_cd_tel']]
        .rename(columns={
            'new_condo_name': 'Condo Name',
            'rent_cd_price': 'Price (THB)',
            'rent_cd_bed': 'Bedrooms',
            'rent_cd_bath': 'Bathrooms',
            'rent_cd_floorarea': 'Area',
            'star': 'Rating',
            'rent_cd_agent': 'Agent',
            'rent_cd_tel': 'Tel'}),
        use_container_width=True
    )

