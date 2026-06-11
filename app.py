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
                "end": m_end.strftime("%d/%m/%Y"), 
                "resource": m_res,
                "status": m_status,
                "type": m_type,
                "parent": m_parent
            })
            st.rerun()
            
    if st.button("🗑️ Reset Workspace"):
        st.session_state.manual_workstreams = []
        st.rerun()
        
    final_df = pd.DataFrame(st.session_state.manual_workstreams)


# --- PROCESSING PIPELINE ENGINE ---
if final_df is not None and not final_df.empty:
    
    final_df['end'] = pd.to_datetime(final_df['end'], dayfirst=True, errors='coerce')
    final_df['start'] = pd.to_datetime(final_df['start'], dayfirst=True, errors='coerce')
    final_df = final_df.dropna(subset=['name', 'end'])
    
    final_df['status'] = final_df['status'].astype(str).str.strip().str.capitalize()
    final_df['type'] = final_df['type'].astype(str).str.strip().str.title()
    final_df['parent'] = final_df['parent'].astype(str).str.strip()
    
    # --- TYPOGRAPHIC HIERARCHY INJECTION FOR AUDIT TABLE ---
    # Custom HTML formatting applied inline to clearly show Tasks vs Sub Tasks
    def apply_html_fonts(row):
        if row['type'] == 'Task':
            # Bold Georgia Serif uppercase for executive Tasks
            return f"<span style='font-family: Georgia, serif; font-weight: bold; color: #2c3e50; font-size: 14px;'>{row['name'].upper()}</span>"
        elif row['type'] == 'Sub Task':
            # Italicized modern clean Sans-Serif for nested Sub Tasks
            return f"<span style='font-family: \"Courier New\", monospace; font-style: italic; color: #555555; padding-left: 15px;'>↳ {row['name']}</span>"
        else:
            return f"<span style='font-family: Arial, sans-serif; font-weight: bold; color: #16a085;'>⭐ {row['name']}</span>"

    st.subheader("📋 Active Workstream Schedule Audit")
    display_df = final_df.copy()
    display_df['Formatted Name'] = display_df.apply(apply_html_fonts, axis=1)
    display_df['start'] = display_df['start'].dt.strftime('%d/%m/%Y').fillna("-")
    display_df['end'] = display_df['end'].dt.strftime('%d/%m/%Y')
    
    # Render with HTML safety turned off to let fonts execute
    st.write(
        display_df.rename(columns={
            "Formatted Name": "Line Item / Deliverable", "start": "Start Date", "end": "End Date", "resource": "Owner/Resource", "status": "Status", "type": "Classification"
        })[["Line Item / Deliverable", "Classification", "Start Date", "End Date", "Owner/Resource", "Status"]].to_html(escape=False, index=False), 
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRAPHIC ENGINE: HIERARCHY MATRIX ---
    st.subheader("📈 Gantt Timeline & Inline Milestone Dependency Graph")
    
    # Separate the elements
    tasks_df = final_df[final_df['type'] == 'Task'].dropna(subset=['start']).copy()
    subtasks_df = final_df[final_df['type'] == 'Sub Task'].dropna(subset=['start']).copy()
    milestones_df = final_df[final_df['type'] == 'Milestone'].copy()

    fig = go.Figure()

    # Color definitions matching status
    status_colors = {
        'Green': '#27ae60',   # Emerald
        'Amber': '#f39c12',   # Warm Orange/Amber
        'Red': '#e74c3c'      # Crimson
    }

    # 1. Plot MAIN TASKS (Colored by Status Column)
    for status_val, color_hex in status_colors.items():
        subset = tasks_df[tasks_df['status'] == status_val]
        if not subset.empty:
            # Calculate duration for plotly base timeline emulation
            for _, row in subset.iterrows():
                fig.add_trace(go.Bar(
                    x=[row['end'] - row['start']],
                    base=[row['start']],
                    y=[row['name']],
                    orientation='h',
                    marker=dict(
                        color=color_hex,
                        line=dict(color='#1a252f', width=1.5)
                    ),
                    name=f"Task: {status_val}",
                    legendgroup=f"task_{status_val}",
                    showlegend=False if f"task_{status_val}" in [t.legendgroup for t in fig.data] else True,
                    hovertemplate=f"<b>{row['name']}</b><br>Owner: {row['resource']}<br>Status: {status_val}<extra></extra>"
                ))

    # 2. Plot SUB TASKS (Light Gray with Dark Blue Border)
    if not subtasks_df.empty:
        for _, row in subtasks_df.iterrows():
            fig.add_trace(go.Bar(
                x=[row['end'] - row['start']],
                base=[row['start']],
                y=[row['name']],
                orientation='h',
                marker=dict(
                    color='#eaeded',      # Soft Premium Light Gray
                    line=dict(color='#1b4f72', width=2) # Deep Dark Blue Outline Border
                ),
                name="Sub Task",
                legendgroup="subtask",
                showlegend=False if "subtask" in [t.legendgroup for t in fig.data] else True,
                hovertemplate=f"<b>Subtask: {row['name']}</b><br>Owner: {row['resource']}<extra></extra>"
            ))

    # 3. Dynamic Inline Milestones Layer
    if not milestones_df.empty:
        today_dt = pd.to_datetime(date.today())
        
        milestones_df['y_axis_target'] = milestones_df.apply(
            lambda r: r['parent'] if (r['parent'] != "" and r['parent'] != "nan") else r['name'], axis=1
        )
        
        green_future = milestones_df
