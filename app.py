import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import mysql.connector
import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from pptx import Presentation
from charts import analyze  # Import từ file charts.py

plt.style.use("ggplot")

def load_file(uploaded_file):
    if uploaded_file is None:
        return pd.DataFrame()
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            content = uploaded_file.read().decode("utf8", errors="ignore")
            rows = []
            for L in content.splitlines():
                parts = L.split()
                if len(parts) < 7:
                    continue
                ip = parts[0]
                time = ""
                if "[" in L:
                    time = L.split("[")[1].split("]")[0]
                req = ""
                try:
                    req = L.split('"')[1]
                except:
                    req = ""
                method, endpoint, proto = (req.split() + ["","",""])[:3]
                status = parts[-2] if parts[-2].isdigit() else ""
                size = parts[-1] if parts[-1].isdigit() else ""
                rows.append((time, ip, method, endpoint, status, size))
            df = pd.DataFrame(rows, columns=["time","ip","method","path","status","size"])
        df["time_parsed"] = pd.to_datetime(df["time"], errors="coerce", infer_datetime_format=True)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame()

def load_mysql(host, user, password, database, query):
    try:
        conn = mysql.connector.connect(
            host=host, user=user, password=password, database=database
        )
        df = pd.read_sql(query, conn)
        conn.close()
        df["time_parsed"] = pd.to_datetime(df["time"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"MySQL error: {e}")
        return pd.DataFrame()

def export_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elems = [
        Paragraph("Log Analyzer Report", styles["Title"]),
        Paragraph(f"Generated: {datetime.datetime.now()}", styles["Normal"]),
        Spacer(1, 12)
    ]
    if "ip" in df:
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
    slide.placeholders[1].text = str(datetime.datetime.now())
    prs.save(buffer)
    buffer.seek(0)
    return buffer

def main():
    st.title("📊 Log Analyzer - Streamlit Edition")

    uploaded_file = st.file_uploader("Upload log file (.log, .txt, .csv)", type=["log","txt","csv"])
    df = load_file(uploaded_file)

    st.subheader("Or connect to MySQL")
    with st.expander("MySQL Connection"):
        host = st.text_input("Host")
        user = st.text_input("User")
        password = st.text_input("Password", type="password")
        database = st.text_input("Database")
        query = st.text_area("Query", "SELECT * FROM logs LIMIT 5000")
        if st.button("Load from MySQL"):
            df = load_mysql(host, user, password, database, query)

    if not df.empty:
        st.subheader("Data Preview")
        flt = st.text_input("Filter keyword")
        df2 = df
        if flt:
            df2 = df2[df2.astype(str).apply(lambda row: row.str.contains(flt, case=False).any(), axis=1)]
        st.dataframe(df2.head(200))

        if st.button("Analyze"):
            analyze(df2)

        pdf_buffer = export_pdf(df2)
        st.download_button("Download PDF", data=pdf_buffer, file_name="report.pdf", mime="application/pdf")

        pptx_buffer = export_pptx()
        st.download_button("Download PPTX", data=pptx_buffer,
                           file_name="report.pptx",
                           mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

if __name__ == "__main__":
    main()
