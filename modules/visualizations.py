import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def smart_parse_time(series):
    t1 = pd.to_datetime(series, format="%d/%b/%Y:%H:%M:%S %z", errors="coerce")
    t2 = pd.to_datetime(series, format="%d/%b/%Y:%H:%M:%S", errors="coerce")
    t3 = pd.to_datetime(series, errors="coerce")
    return t1.fillna(t2).fillna(t3)

def analyze(df):
    if df.empty:
        st.warning("No data loaded")
        return

    df["time_parsed"] = smart_parse_time(df["time"])
    if df["time_parsed"].isna().all():
        st.warning("Không có timestamp hợp lệ trong log!")
        return

    # Biểu đồ 1: Top IP nghi vấn (Request nhiều)
    top_ip = df["ip"].value_counts().head(10)

    # Biểu đồ 2: Top IP gây lỗi 404
    df_404 = df[df["status"] == "404"]
    top_404_ip = df_404["ip"].value_counts().head(10)

    # Pie chart tổng hợp mã lỗi
    status_counts = df["status"].value_counts()
    status_labels = status_counts.index.tolist()
    status_values = status_counts.values.tolist()

    fig, axes = plt.subplots(1, 2, figsize=(14,6))

    # Biểu đồ ngang: Top IP nghi vấn
    axes[0].barh(top_ip.index[::-1], top_ip.values[::-1], color="salmon")
    axes[0].set_title("Top IP nghi vấn (Request nhiều)", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Số lượng request")
    axes[0].grid(axis="x", linestyle="--", alpha=0.5)

    # Donut chart: Mã lỗi
    wedges, texts, autotexts = axes[1].pie(status_values, labels=status_labels, autopct='%1.1f%%', startangle=90)
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    axes[1].add_artist(centre_circle)
    axes[1].set_title("Tỷ lệ mã lỗi (Dò quét)", fontsize=12, fontweight="bold")

    st.pyplot(fig)

    # Bảng phụ: Top IP gây lỗi 404
    st.subheader("🔍 Top IP gây lỗi 404 (Dò quét)")
    st.table(top_404_ip.reset_index().rename(columns={"index":"IP", "ip":"Số lỗi 404"}))

# Biểu đồ và đồ thị 
