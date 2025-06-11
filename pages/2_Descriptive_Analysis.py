import pandas as pd
import streamlit as st
import plotly.express as px

@st.cache_data
def load_data():
    return pd.read_csv('data_cleaned.csv')

df = load_data()

st.title('Page 2 : Descriptive Analysis')

numeric_cols = df.select_dtypes(include='number').columns.tolist()

column = st.selectbox('Select column to analyze', df.columns)

if column in numeric_cols:
    chart_type = st.radio('Chart type', ['Histogram', 'Box Plot'], horizontal=True)
    if chart_type == 'Histogram':
        fig = px.histogram(df, x=column, nbins=30, title=f'Histogram of {column}')
    else:
        fig = px.box(df, y=column, title=f'Box Plot of {column}')
    st.plotly_chart(fig, use_container_width=True)
else:
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, 'count']
    fig = px.bar(counts, x=column, y='count', title=f'Bar Chart of {column}')
    st.plotly_chart(fig, use_container_width=True)
