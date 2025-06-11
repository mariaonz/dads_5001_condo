import pandas as pd
import streamlit as st
import duckdb
import os

# ตั้งค่า layout
st.set_page_config(page_title="Smart Rent BKK", page_icon="🌆", layout="wide")

# เฟื่อตำประมวล DuckDB จาก CSV
@st.cache_data
def create_duckdb_from_csv():
    if not os.path.exists("condo.duckdb"):
        df = pd.read_csv("data_cleaned.csv")
        con = duckdb.connect("condo.duckdb")
        con.execute("DROP TABLE IF EXISTS condo")
        con.execute("CREATE TABLE condo AS SELECT * FROM df")
        con.close()
        return "created"
    else:
        return "exists"

# ดึงข้อมูลจาก duckdb
@st.cache_data
def load_data_from_duckdb():
    con = duckdb.connect("condo.duckdb")
    df = con.execute("SELECT * FROM condo").df()
    con.close()
    return df

# แปลงรายงเป็นดาวน์
def convert_for_download(df):
    return df.to_csv(index=False).encode("utf-8")

# แปลงระดับเป็นดาวแสดง
def rating_to_stars(rating, max_stars=5):
    if pd.isna(rating):
        return "N/A"
    integer_part = int(rating)
    decimal_part = rating - integer_part
    full_stars = "⭐" * integer_part
    half_star = "½" if decimal_part >= 0.5 else ""
    empty_stars = "☆" * (max_stars - integer_part - (1 if decimal_part >= 0.5 else 0))
    return full_stars + half_star + empty_stars

# === MAIN PAGE ===
def main_page():
    status = create_duckdb_from_csv()
    df = load_data_from_duckdb()

    st.title("Smart Rent BKK 🌆")
    st.caption("(Data source: DuckDB from data_cleaned.csv)")

    st.image("https://raw.githubusercontent.com/ppitchaporn/DADS5001-Condo/a785a69fe796a14d3023d993a8c89289c4bd067a/Condo_image.jpg")

    options = [5, 10, 25, 50, 100, "All"]
    selection_rows = st.pills("Select Top Rows:", options, selection_mode="single", default=5)
    st.markdown(f"Displaying {selection_rows} rows.")

    df_display = df.copy()
    if selection_rows != "All":
        df_display = df_display.head(int(selection_rows))

    df_display['Rating'] = df_display['star'].apply(rating_to_stars)

    st.dataframe(
        df_display,
        column_config={
            "Rating": st.column_config.Column("Rating", help="คะแนนรีวิว", width="small"),
            "star": None
        },
        column_order=[
            "condo_name", "Rating", "rent_cd_address", "rent_cd_price",
            "rent_cd_bed", "rent_cd_bath", "rent_cd_features_station",
            "near_rail_meter", "rent_cd_features_time"
        ],
        hide_index=True
    )

    # Download button
    csv = convert_for_download(df)
    st.download_button("Download CSV", data=csv, file_name="data.csv", mime="text/csv")

    # Footer
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Name")
        st.write("Mr.Kitisak Namtae")
        st.write("Mr.Kantapong Charusiri")
        st.write("Miss Pitchaporn Nimdum")
        st.write("Miss Pornchanok Tuntikulwattanakit")
        st.write("Mr.Suparerk Jankam")
    with col2:
        st.subheader("ID")
        st.write("6710422007")
        st.write("6710422015")
        st.write("6710422016")
        st.write("6710422023")
        st.write("6710422028")

    st.subheader("Rate Us")
    sentiment_mapping = ["one", "two", "three", "four", "five"]
    selected = st.feedback("stars")
    if selected is not None:
        st.markdown(f"You selected {sentiment_mapping[selected]} star(s). \n Thank You. 😊")

# === Page navigation ===
#home_page = st.Page(main_page, title='Home page', icon=":material/home:")
#descipt = st.Page("page2.py", title='Descriptive Analysis', icon=":material/database:")
#relation_predict = st.Page("page3.py", title='Relationship Analysis & Price Prediction', icon=":material/bar_chart:")
#geospatial_class = st.Page("page4.py", title='Geospatial Analysis & Classification Result', icon=":material/bar_chart:")
#Ai_search = st.Page("page5.py", title=' Advanced Search & Comparison', icon=":material/note:")

#pg = st.navigation({"Menu": [home_page, descipt, relation_predict, geospatial_class, Ai_search]})
#pg.run()

# === MAIN ===
if __name__ == '__main__':
    main_page()
