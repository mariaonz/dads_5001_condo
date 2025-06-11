import pandas as pd
import streamlit as st
import plotly.express as px

@st.cache_data
def load_data():
    return pd.read_csv('data_cleaned.csv')

def main():
    st.set_page_config(page_title='Condo Rental Explorer', layout='wide')
    df = load_data()

    st.title('Condo Rental Explorer')
    st.write('Explore condominium rental listings in Bangkok.')

    st.subheader('Dataset Preview')
    st.dataframe(df.head())

    st.subheader('Price Distribution')
    fig_hist = px.histogram(df, x='rent_cd_price', nbins=40,
                            labels={'rent_cd_price': 'Rental Price (THB)'},
                            title='Distribution of Rental Prices')
    st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader('Price vs. Floor Area')
    bed_options = sorted(df['rent_cd_bed'].dropna().unique())
    selected_beds = st.multiselect('Bedrooms', bed_options, default=bed_options)
    filtered = df[df['rent_cd_bed'].isin(selected_beds)]
    fig_scatter = px.scatter(filtered, x='rent_cd_floorarea', y='rent_cd_price',
                             color='rent_cd_bed',
                             labels={'rent_cd_floorarea': 'Floor Area (sqm)',
                                     'rent_cd_price': 'Rental Price (THB)',
                                     'rent_cd_bed': 'Bedrooms'},
                             title='Price vs. Floor Area')
    st.plotly_chart(fig_scatter, use_container_width=True)

if __name__ == '__main__':
    main()
