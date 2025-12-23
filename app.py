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
from modules.database import save_log_data, get_data_to_dataframe, get_logs_by_filters, clear_all_logs, get_statistics

load_dotenv()

plt.style.use("ggplot")

st.set_page_config(page_title="Log Analyzer Pro", layout="wide", initial_sidebar_state="expanded")

# Session state
if "df_global" not in st.session_state:
    st.session_state.df_global = pd.DataFrame()
if "data_source" not in st.session_state:
    st.session_state.data_source = "memory"

def page_dashboard(df):
    st.title("📊 Dashboard")
    
    if df.empty:
        st.info("Upload a log file or load from database to get started")
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
    
    st.divider()
    
    # Database statistics
    with st.expander("📊 Database Statistics"):
        try:
            stats = get_statistics()
            if stats:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total in DB", f"{stats.get('total_logs', 0):,}")
                with col2:
                    st.metric("Errors", f"{stats.get('error_count', 0):,}")
                with col3:
                    st.metric("Warnings", f"{stats.get('warning_count', 0):,}")
                with col4:
                    st.metric("Info", f"{stats.get('info_count', 0):,}")
        except:
            st.warning("Could not retrieve database statistics")

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
    
    # Export to CSV
    csv = df_filtered.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="logs_filtered.csv",
        mime="text/csv"
    )

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

def page_database():
    """Page để quản lý Database"""
    st.title("🗄️ Database Management")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Load from database
    with col1:
        if st.button("📥 Load from Database", use_container_width=True):
            with st.spinner("Loading data from database..."):
                df = get_data_to_dataframe()
                if not df.empty:
                    st.session_state.df_global = df
                    st.session_state.data_source = "database"
                    st.success(f"✅ Loaded {len(df):,} records from database")
                    st.rerun()
                else:
                    st.warning("Database is empty")
    
    # Save to database
    with col2:
        if st.button("💾 Save to Database", use_container_width=True):
            if st.session_state.df_global.empty:
                st.warning("No data in memory to save")
            else:
                with st.spinner("Saving to database..."):
                    df = st.session_state.df_global
                    data_list = [
                        (row["ip"], row.get("timestamp"), row["status"], 
                         row.get("log_level", "INFO"), row.get("response", ""))
                        for _, row in df.iterrows()
                    ]
                    if save_log_data(data_list):
                        st.success(f"✅ Saved {len(df):,} records to database")
                        st.rerun()
    
    # Clear database
    with col3:
        if st.button("🗑️ Clear Database", use_container_width=True):
            if st.checkbox("⚠️ Confirm delete all records", key="confirm_delete"):
                with st.spinner("Clearing database..."):
                    if clear_all_logs():
                        st.success("✅ Database cleared")
                        st.rerun()
    
    # View statistics
    with col4:
        if st.button("📊 View Statistics", use_container_width=True):
            try:
                stats = get_statistics()
                if stats:
                    st.json(stats)
                else:
                    st.info("No statistics available")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.divider()
    
    # Advanced filter
    st.subheader("🔍 Advanced Filter")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("From Date")
    
    with col2:
        end_date = st.date_input("To Date")
    
    with col3:
        log_level = st.selectbox("Log Level", ["All", "INFO", "WARNING", "ERROR"])
    
    if st.button("🔎 Filter Data", use_container_width=True):
        log_level_filter = None if log_level == "All" else log_level
        df_filtered = get_logs_by_filters(
            start_date=str(start_date),
            end_date=str(end_date),
            log_level=log_level_filter
        )
        
        if not df_filtered.empty:
            st.session_state.df_global = df_filtered
            st.session_state.data_source = "database_filtered"
            st.success(f"✅ Loaded {len(df_filtered):,} filtered records")
            st.rerun()
        else:
            st.info("No records found with these filters")

def main():
    st.sidebar.title("📊 Log Analyzer Pro")
    st.sidebar.markdown("---")
    
    # File uploader
    uploaded_file = st.sidebar.file_uploader("Upload log file", type=["log", "txt", "csv"])
    
    if uploaded_file:
        with st.spinner("Processing file..."):
            data_list, stats = parse_log_file(uploaded_file)
            if data_list:
                df = pd.DataFrame(data_list, columns=["ip", "timestamp", "status", "log_level", "response"])
                st.session_state.df_global = df
                st.session_state.data_source = "memory"
                st.sidebar.success(f"✅ Loaded {len(df):,} records")
                
                # Auto-save option
                if st.sidebar.checkbox("💾 Auto-save to Database", value=False):
                    with st.spinner("Saving to database..."):
                        if save_log_data(data_list):
                            st.sidebar.success("✅ Saved to database")
    
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.radio("Navigation", [
        "Dashboard",
        "Data Logs",
        "Notifications",
        "Database"
    ], label_visibility="collapsed")
    
    st.sidebar.markdown("---")
    
    # Page routing
    if page == "Dashboard":
        page_dashboard(st.session_state.df_global)
    elif page == "Data Logs":
        page_data_logs(st.session_state.df_global)
    elif page == "Notifications":
        page_notifications(st.session_state.df_global)
    elif page == "Database":
        page_database()
    
    # 🔧 DATA SOURCE INDICATOR - ĐẶT SAU PAGE ROUTING
    st.sidebar.markdown("---")
    if not st.session_state.df_global.empty:
        st.sidebar.info(
            f"📍 Source: {st.session_state.data_source.upper()}\n"
            f"Records: {len(st.session_state.df_global):,}"
        )
    
    st.sidebar.caption("Log Analyzer Pro v1.1")

if __name__ == "__main__":
    main()