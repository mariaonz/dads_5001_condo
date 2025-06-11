import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

df = load_data('data_cleaned.csv')

st.title('Condo Rent Visualization')

# Filters
bed_options = sorted(df['rent_cd_bed'].dropna().unique())
selected_bed = st.selectbox('Number of Bedrooms', options=bed_options)

price_min, price_max = int(df['rent_cd_price'].min()), int(df['rent_cd_price'].max())
price_range = st.slider('Price Range', min_value=price_min, max_value=price_max,
                        value=(price_min, price_max))

filtered = df[(df['rent_cd_bed'] == selected_bed) &
              (df['rent_cd_price'].between(*price_range))]

fig = px.scatter(
    filtered,
    x='rent_cd_bed',
    y='rent_cd_price',
    color='rent_cd_bed',
    hover_data=['rent_cd_address'],
    labels={'rent_cd_bed': 'Bedrooms', 'rent_cd_price': 'Price'},
    title='Price vs Bedrooms'
)

st.plotly_chart(fig, use_container_width=True)
