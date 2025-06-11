import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from pymongo import MongoClient

st.set_page_config(page_title=" [BTS/MRT] Proximity vs Rent Price", layout="wide")

@st.cache_data

#CSV
#def load_data():
#    return pd.read_csv('https://raw.githubusercontent.com/ppitchaporn/DADS5001-Condo/refs/heads/main/data_cleaned.csv')

#No-SQL - MongoDB
def load_data():
    
    mongo_uri = st.secrets["MONGO_URI"]
    
    client = MongoClient(mongo_uri)
    db = client["data_cleaned"]
    collection = db["data_cleaned"]
    
    data = list(collection.find())
    
    df = pd.DataFrame(data)
    
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
    
    return df



df_raw = load_data()

# === Sidebar ===
st.sidebar.header("🔎 Filters")

remove_outliers = st.sidebar.checkbox("Remove Outliers (P5–P95)", value=True)

if remove_outliers:
    p5 = df_raw["rent_cd_price"].quantile(0.05)
    p95 = df_raw["rent_cd_price"].quantile(0.95)
    df = df_raw[(df_raw["rent_cd_price"] >= p5) & (df_raw["rent_cd_price"] <= p95)]
else:
    df = df_raw.copy()

df_near = df.dropna(subset=["near_rail_meter", "rent_cd_price"]).copy()

bins = [0, 300, 700, df_near["near_rail_meter"].max()]
labels = ["Near (<300m)", "Mid (300-700m)", "Far (>700m)"]
df_near["rail_distance_group"] = pd.cut(df_near["near_rail_meter"], bins=bins, labels=labels)

df_near["condo_display_name"] = df_near.apply(
    lambda row: f"{row['condo_name']} ({row['rent_cd_features_station']})"
    if pd.notnull(row['rent_cd_features_station']) else row['condo_name'],
    axis=1
)

condo_display_map = dict(zip(df_near["condo_display_name"], df_near["condo_name"]))
condo_options = sorted(condo_display_map.keys())

selected_groups = st.sidebar.multiselect(
    "Select [BTS/MRT] distance groups", options=labels, default=labels
)
selected_display_names = st.sidebar.multiselect(
    "Select condo names (optional)", options=condo_options
)
selected_condos = [condo_display_map[name] for name in selected_display_names]

filtered_df = df_near[df_near["rail_distance_group"].isin(selected_groups)]
if selected_condos:
    filtered_df = filtered_df[filtered_df["condo_name"].isin(selected_condos)]

# === MAIN ===
st.title("🚉 Descriptive Analysis")
st.caption(f"Outliers removed: {remove_outliers}")

st.subheader("📈 Rent Price vs Distance to [BTS/MRT] (Scatter Plot)")
fig_scatter = px.scatter(
    filtered_df, x="near_rail_meter", y="rent_cd_price",
    trendline="ols", color="rail_distance_group",
    hover_data=["condo_name", "rent_cd_features_station"],
    labels={"near_rail_meter": "Distance to [BTS/MRT] (m)", "rent_cd_price": "Rent Price (THB)"},
    title="Relationship between Rent Price and Distance to [BTS/MRT]"
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.subheader("📦 Rent Price by Distance Group (Boxplot)")
fig_box = px.box(
    filtered_df, x="rail_distance_group", y="rent_cd_price",
    color="rail_distance_group",
    title="Rent Price by [BTS/MRT] Distance Group",
    labels={"rail_distance_group": "Distance Group", "rent_cd_price": "Rent Price (THB)"}
)
st.plotly_chart(fig_box, use_container_width=True)

with st.expander("📊 Summary Statistics by [BTS/MRT] Distance", expanded=True):
    summary = filtered_df.groupby("rail_distance_group")["rent_cd_price"].agg(
        count="count",
        mean="mean",
        median="median",
        std="std",
        min_val="min",
        max_val="max"
    ).reset_index()

    summary["CV (%)"] = (summary["std"] / summary["mean"]) * 100
    summary["Range"] = summary.apply(
        lambda row: f"{int(row['min_val']):,}–{int(row['max_val']):,}"
        if pd.notnull(row["min_val"]) and pd.notnull(row["max_val"])
        else "N/A", axis=1
    )

    summary = summary[["rail_distance_group", "count", "mean", "median", "std", "CV (%)", "Range"]]
    summary.columns = ["[BTS/MRT] Distance", "Count", "Avg", "Median", "Std Dev", "CV (%)", "Range"]

    for col in ["Avg", "Median", "Std Dev", "CV (%)"]:
        summary[col] = pd.to_numeric(summary[col], errors="coerce")

    st.dataframe(summary.style.format({
        "Avg": "{:,.0f}",
        "Median": "{:,.0f}",
        "Std Dev": "{:,.0f}",
        "CV (%)": "{:,.1f}"
    }))
    st.caption("💡 CV = ความผันผวนในแต่ละกลุ่ม  •  Range = ราคาเช่าต่ำ–สูง")

# === Insight Layer & Recommendation ===
with st.expander("🏢 Compare Selected Condos by Average Price", expanded=True):
    if selected_condos:
        condo_compare = filtered_df.groupby("condo_name")["rent_cd_price"].agg(
            count="count", mean="mean", median="median"
        ).reset_index().sort_values("mean", ascending=False)

        overall_avg = filtered_df["rent_cd_price"].mean()
        overall_std = filtered_df["rent_cd_price"].std()

        condo_compare["z_score"] = (condo_compare["mean"] - overall_avg) / overall_std
        condo_compare["value_tag"] = condo_compare["z_score"].apply(
            lambda z: "✅ Good Deal" if z <= -0.75 else ("⚠️ Too Expensive" if z >= 0.75 else "Fair")
        )

        fig_bar = px.bar(
            condo_compare, x="condo_name", y="mean",
            hover_data=["count", "median", "z_score", "value_tag"],
            color="value_tag",
            title="Average Rent Price by Condo (with Value Assessment)",
            labels={"condo_name": "Condo Name", "mean": "Average Rent (THB)", "value_tag": "Value Category"}
        )
        fig_bar.add_hline(y=overall_avg, line_dash="dot", line_color="gray",
                          annotation_text="Overall Market Avg", annotation_position="top left")

        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Please select at least one condo to compare.")

# 🧠 Recommendation Panel
with st.expander("💡 Recommended Condos Based on Price-to-Market", expanded=True):
    if selected_condos and "condo_compare" in locals():
        good_deals = condo_compare[condo_compare["value_tag"] == "✅ Good Deal"]
        if not good_deals.empty:
            st.write("🎯 Condos with significantly lower average rent compared to market average:")
            st.dataframe(good_deals[["condo_name", "mean", "median", "z_score", "value_tag"]].round(2))
        else:
            st.info("No condos currently meet the 'Good Deal' threshold.")
        
        st.caption("""
        **Z-Score-based Value Tags:**
        - ✅ **Good Deal**: Average rent is significantly below market average *(z-score ≤ -0.75)*
        - ⚠️ **Too Expensive**: Rent exceeds market average substantially *(z-score ≥ +0.75)*
        - **Fair**: Rent is within expected market range
        """)
    else:
        st.info("Please select condos first to generate recommendation.")

with st.expander("🚉 Average Rent by [BTS/MRT] Station", expanded=True):
    station_avg = filtered_df.dropna(subset=["rent_cd_features_station"]).groupby(
        "rent_cd_features_station"
    )["rent_cd_price"].agg(
        count="count", mean="mean", median="median"
    ).reset_index().sort_values("mean", ascending=False)

    fig_station = px.bar(
        station_avg, x="rent_cd_features_station", y="mean",
        hover_data=["count", "median"],
        title="Average Rent by [BTS/MRT] Station",
        labels={
            "rent_cd_features_station": "[BTS/MRT] Station",
            "mean": "Average Rent (THB)",
            "count": "Number of Units",
            "median": "Median Rent"
        }
    )
    st.plotly_chart(fig_station, use_container_width=True)
