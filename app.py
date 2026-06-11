import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

st.set_page_config(page_title="Hierarchical Workstream Matrix", layout="wide")

st.title("📊 Enterprise Hierarchical Workstream & Milestone Matrix")
st.markdown("Upload your structured schedule spreadsheet (**DD/MM/YYYY**). Main Tasks are colored by status. Sub Tasks are gray with dark blue borders. Milestones are plotted directly inline on parent task lines.")

# --- SIDEBAR: DATA UPLOAD & SOURCE MANAGEMENT ---
st.sidebar.header("📁 Data Source Configuration")
upload_mode = st.sidebar.radio("Choose Input Method:", ["Upload Spreadsheet (Excel / CSV)", "Manual Live Entry"])

# Demo dataset reflecting structural mapping hierarchy and custom styles
demo_data = [
    {"name": "1.0 Core Architecture Framework", "start": "01/07/2026", "end": "30/07/2026", "resource": "Product Team", "status": "Green", "type": "Task", "parent": ""},
    {"name": "   1.1 Competitor Benchmarking", "start": "01/07/2026", "end": "12/07/2026", "resource": "Product Team", "status": "Green", "type": "Sub Task", "parent": "1.0 Core Architecture Framework"},
    {"name": "   1.2 User Persona Survey Pool", "start": "10/07/2026", "end": "28/07/2026", "resource": "Design Studio", "status": "Amber", "type": "Sub Task", "parent": "1.0 Core Architecture Framework"},
    {"name": "⭐ Phase 1 Strategy Sign-Off Gate", "start": "", "end": "15/07/2026", "resource": "Product Team", "status": "Green", "type": "Milestone", "parent": "1.0 Core Architecture Framework"}, 
    
    {"name": "2.0 Database Core Implementation", "start": "15/07/2026", "end": "15/08/2026", "resource": "Dev Engineering", "status": "Red", "type": "Task", "parent": ""},
    {"name": "   2.1 Schema Definition & Mapping", "start": "15/07/2026", "end": "02/08/2026", "resource": "Dev Engineering", "status": "Green", "type": "Sub Task", "parent": "2.0 Database Core Implementation"},
    {"name": "🚩 Security Audit Clearance Review", "start": "", "end": "20/07/2026", "resource": "QA Automation", "status": "Green", "type": "Milestone", "parent": "2.0 Database Core Implementation"} 
]

final_df = None

if upload_mode == "Upload Spreadsheet (Excel / CSV)":
    st.sidebar.subheader("Excel / CSV Uploader")
    uploaded_file = st.sidebar.file_uploader(
        "Upload file (Required columns: Workstream Name, Start Date, End Date, Assigned Resource, Status, Type, Parent Task)", 
        type=["xlsx", "csv"]
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                raw_df = pd.read_csv(uploaded_file)
            else:
                raw_df = pd.read_excel(uploaded_file)
            
            rename_map = {
                "Workstream Name": "name", "workstream name": "name", "Workstream": "name", "name": "name",
                "Start Date": "start", "start date": "start", "Start": "start", "start": "start",
                "End Date": "end", "end date": "end", "End": "end", "end": "end",
                "Assigned Resource": "resource", "assigned resource": "resource", "Resource": "resource", "resource": "resource",
                "Status": "status", "status": "status", "STATUS": "status",
                "Type": "type", "type": "type", "TYPE": "type",
                "Parent Task": "parent", "parent task": "parent", "Parent": "parent", "parent": "parent"
            }
            raw_df = raw_df.rename(columns=rename_map)
            
            required_cols = ['name', 'start', 'end', 'resource', 'status', 'type', 'parent']
            if all(col in raw_df.columns for col in required_cols):
                final_df = raw_df[required_cols].dropna(subset=['name', 'end']).copy()
                st.sidebar.success("✅ Dataset parsed successfully!")
            else:
                missing = [c for c in required_cols if c not in raw_df.columns]
                st.sidebar.error(f"❌ Missing columns: {missing}")
        except Exception as e:
            st.sidebar.error(f"File system parse error: {e}")
    else:
        st.info("👋 Displaying structural demo hierarchy data.")
        final_df = pd.DataFrame(demo_data)

else:
    if "manual_workstreams" not in st.session_state:
        st.session_state.manual_workstreams = demo_data.copy()
        
    st.sidebar.subheader("Create Row Entry")
    m_name = st.sidebar.text_input("Item Name")
    m_res = st.sidebar.text_input("Assigned Owner", placeholder="e.g., DevOps")
    m_start = st.sidebar.date_input("Start Date (Ignored for Milestones)", datetime.today())
    m_end = st.sidebar.date_input("End Date / Milestone Date", datetime.today())
    m_status = st.sidebar.selectbox("Status", ["Green", "Amber", "Red"])
    m_type = st.sidebar.selectbox("Classification", ["Task", "Sub Task", "Milestone"])
    m_parent = st.sidebar.text_input("Parent Task Name (Required for Sub Tasks & Milestones)")
    
    if st.sidebar.button("Add Item Row"):
        if m_name:
            st.session_state.manual_workstreams.append({
                "name": m_name, 
                "start": m_start.strftime("%d/%m/%Y") if m_type != "Milestone" else "", 
                "end": m_end
