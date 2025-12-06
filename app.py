import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from io import BytesIO
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from pptx import Presentation
from modules.charts import analyze
from modules.log_parser import parse_log_file

load_dotenv()

plt.style.use("ggplot")

st.set_page_config(page_title="Log Analyzer Pro", layout="wide", initial_sidebar_state="expanded")

df_global = pd.DataFrame()

def export_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elems = [
        Paragraph("Log Analyzer Report", styles["Title"]),
        Spacer(1, 12)
    ]
    if "ip" in df.columns:
        top = df["ip"].value_counts().head(10).reset_index()
        top.columns = ["ip", "count"]
        elems.append(Table([top.columns.tolist()] + top.values.tolist()))
    doc.build(elems)
    buffer.seek(0)
    return buffer

def export_pptx():
    buffer = BytesIO()
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Log Analyzer Report"
    prs.save(buffer)
    buffer.seek(0)
    return buffer

def page_dashboard(df):
    st.title("📊 Dashboard")
    
    if df.empty:
        st.info("Upload a log file to get started")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Requests", f"{len(df):,}")
    
    with col2:
        error_count = len(df[df["status"] >= 400])
        error_rate = (error_count / len(df) * 100) if len(df) > 0 else 0
        st.metric("Error Rate", f"{error_rate:.1f}%")
    
    with col3:
        unique_ips = df["ip"].nunique()
        st.metric("Unique IPs", f"{unique_ips:,}")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        top_ip = df["ip"].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(top_ip.index[::-1], top_ip.values[::-1], color="#FF6B6B")
        ax.set_title("Top 10 IPs by Requests", fontweight="bold", fontsize=14)
        ax.set_xlabel("Number of Requests")
        ax.grid(axis="x", alpha=0.3)
        st.pyplot(fig, use_container_width=True)
    
    with col2:
        status_counts = df["status"].value_counts()
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ["#51CF66", "#FFD93D", "#FF6B6B", "#845EC2"]
        wedges, texts, autotexts = ax.pie(status_counts.values, labels=status_counts.index, 
                                           autopct='%1.1f%%', colors=colors[:len(status_counts)], textprops={'fontsize': 10})
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        ax.add_artist(centre_circle)
        ax.set_title("HTTP Status Code Distribution", fontweight="bold", fontsize=14)
        st.pyplot(fig, use_container_width=True)

def page_data_logs(df):
    st.title("📋 Data Logs")
    
    if df.empty:
        st.info("No data loaded")
        return
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        flt = st.text_input("🔍 Search", placeholder="Search by IP or status...")
    
    with col2:
        status_filter = st.selectbox("Filter Status", ["All"] + sorted(df["status"].unique().astype(str).tolist()))
    
    with col3:
        level_filter = st.selectbox("Log Level", ["All"] + df["log_level"].unique().tolist() if "log_level" in df.columns else ["All"])
    
    df_filtered = df
    
    if flt:
        df_filtered = df_filtered[df_filtered.astype(str).apply(lambda row: row.str.contains(flt, case=False).any(), axis=1)]
    
    if status_filter != "All":
        df_filtered = df_filtered[df_filtered["status"].astype(str) == status_filter]
    
    if level_filter != "All" and "log_level" in df.columns:
        df_filtered = df_filtered[df_filtered["log_level"] == level_filter]
    
    st.dataframe(df_filtered, use_container_width=True, height=400)
    st.caption(f"Showing {len(df_filtered)} of {len(df)} records")

def page_notifications(df):
    st.title("⚠️ Notifications")
    
    if df.empty:
        st.info("No data loaded")
        return
    
    error_logs = df[df["status"] >= 500]
    warning_logs = df[(df["status"] >= 400) & (df["status"] < 500)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.error(f"🔴 Server Errors (5xx): {len(error_logs)}")
        if not error_logs.empty:
            st.dataframe(error_logs[["ip", "status", "timestamp"]], use_container_width=True)
        else:
            st.success("No server errors")
    
    with col2:
        st.warning(f"🟠 Client Errors (4xx): {len(warning_logs)}")
        if not warning_logs.empty:
            st.dataframe(warning_logs[["ip", "status", "timestamp"]], use_container_width=True)
        else:
            st.success("No client errors")

def main():
    st.sidebar.title("📊 Log Analyzer Pro")
    st.sidebar.markdown("---")
    
    uploaded_file = st.sidebar.file_uploader("Upload log file", type=["log", "txt", "csv"])
    
    global df_global
    
    if uploaded_file:
        with st.spinner("Processing file..."):
            data_list, stats = parse_log_file(uploaded_file)
            if data_list:
                df_global = pd.DataFrame(data_list, columns=["ip", "timestamp", "status", "log_level", "response"])
                st.sidebar.success(f"✅ Loaded {len(df_global)} records")
    
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio("Navigation", [
        "Dashboard",
        "Data Logs",
        "Notifications"
    ], label_visibility="collapsed")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Log Analyzer Pro v1.0")
    
    if page == "Dashboard":
        page_dashboard(df_global)
    elif page == "Data Logs":
        page_data_logs(df_global)
    elif page == "Notifications":
        page_notifications(df_global)

if __name__ == "__main__":
    main()