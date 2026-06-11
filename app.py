import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Workstream Visualizer & Milestones Engine", layout="wide")

st.title("📊 Enterprise Workstream Visualizer & Milestone Timeline Matrix")
st.markdown("Upload your hierarchy spreadsheet (**DD/MM/YYYY** dates). **Tasks** and **Sub Tasks** render as floating timeline tracks, while **Milestones** render as sharp structural triangles or green completion checkmarks.")

# --- SIDEBAR: DATA UPLOAD & SOURCE MANAGEMENT ---
st.sidebar.header("📁 Data Source Configuration")
upload_mode = st.sidebar.radio("Choose Input Method:", ["Upload Spreadsheet (Excel / CSV)", "Manual Live Entry"])

# Robust demo dataset illustrating Task, Sub Task, and Milestone structural mapping
demo_data = [
    {"name": "1.0 Core Market Analysis Framework", "start": "01/07/2026", "end": "15/07/2026", "resource": "Product Team", "status": "Green", "type": "Task"},
    {"name": "   1.1 Competitor Benchmarking", "start": "01/07/2026", "end": "08/07/2026", "resource": "Product Team", "status": "Green", "type": "Sub Task"},
    {"name": "   1.2 User Persona Survey Pool", "start": "06/07/2026", "end": "14/07/2026", "resource": "Design Studio", "status": "Amber", "type": "Sub Task"},
    {"name": "⭐ Phase 1 Strategy Sign-Off Gate", "start": "15/07/2026", "end": "15/07/2026", "resource": "Product Team", "status": "Green", "type": "Milestone"}, # COMPLETED (Green Status) -> Render Green Checkmark
    
    {"name": "2.0 System Architecture & Backend Base", "start": "15/07/2026", "end": "15/08/2026", "resource": "Dev Engineering", "status": "Amber", "type": "Task"},
    {"name": "   2.1 Database Schema Mapping", "start": "15/07/2026", "end": "28/07/2026", "resource": "Dev Engineering", "status": "Green", "type": "Sub Task"},
    {"name": "   2.2 Auth API Integration Endpoints", "start": "25/07/2026", "end": "12/08/2026", "resource": "Dev Engineering", "status": "Red", "type": "Sub Task"},
    {"name": "🚩 Security Audit Clearance Review", "start": "15/08/2026", "end": "15/08/2026", "resource": "QA Automation", "status": "Amber", "type": "Milestone"}  # INCOMPLETE (Amber/Red Status) -> Render Triangle
]

final_df = None

if upload_mode == "Upload Spreadsheet (Excel / CSV)":
    st.sidebar.subheader("Excel / CSV Uploader")
    uploaded_file = st.sidebar.file_uploader(
        "Upload file (Required: Workstream Name, Start Date, End Date, Assigned Resource, Status, Type)", 
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
                "Type": "type", "type": "type", "TYPE": "type"
            }
            raw_df = raw_df.rename(columns=rename_map)
            
            required_cols = ['name', 'start', 'end', 'resource', 'status', 'type']
            if all(col in raw_df.columns for col in required_cols):
                final_df = raw_df[required_cols].dropna(subset=['name', 'start', 'end']).copy()
                st.sidebar.success("✅ Architecture dataset parsed successfully!")
            else:
                missing = [c for c in required_cols if c not in raw_df.columns]
                st.sidebar.error(f"❌ Column Mapping Error. Missing fields: {missing}")
        except Exception as e:
            st.sidebar.error(f"File system parse crash: {e}")
    else:
        st.info("👋 Displaying structural demo hierarchy data. Drag your active tracking schedule spreadsheet into the sidebar uploader box.")
        final_df = pd.DataFrame(demo_data)

else:
    if "manual_workstreams" not in st.session_state:
        st.session_state.manual_workstreams = demo_data.copy()
        
    st.sidebar.subheader("Create Hierarchical Row Entry")
    m_name = st.sidebar.text_input("Row Name (e.g.,   1.1 Subtask Alpha)")
    m_res = st.sidebar.text_input("Assigned Team Pool", placeholder="e.g., DevOps Group")
    m_start = st.sidebar.date_input("Start Date Anchor", datetime.today())
    m_end = st.sidebar.date_input("End Date Anchor", datetime.today())
    m_status = st.sidebar.selectbox("Status Color Map", ["Green", "Amber", "Red"])
    m_type = st.sidebar.selectbox("Structural Classification Type", ["Task", "Sub Task", "Milestone"])
    
    if st.sidebar.button("Add Item Row"):
        if m_name and m_res:
            st.session_state.manual_workstreams.append({
                "name": m_name, 
                "start": m_start.strftime("%d/%m/%Y"), 
                "end": m_end.strftime("%d/%m/%Y"), 
                "resource": m_res,
                "status": m_status,
                "type": m_type
            })
            st.rerun()
            
    if st.button("🗑️ Reset Tracking Table Workspace"):
        st.session_state.manual_workstreams = []
        st.rerun()
        
    final_df = pd.DataFrame(st.session_state.manual_workstreams)


# --- PROCESSING PIPELINE ENGINE ---
if final_df is not None and not final_df.empty:
    
    # Strictly handle DD/MM/YYYY formatting logic constraint
    final_df['start'] = pd.to_datetime(final_df['start'], dayfirst=True, errors='coerce')
    final_df['end'] = pd.to_datetime(final_df['end'], dayfirst=True, errors='coerce')
    final_df = final_df.dropna(subset=['start', 'end'])
    
    # Text standardization rules
    final_df['status'] = final_df['status'].astype(str).str.strip().str.capitalize()
    final_df['type'] = final_df['type'].astype(str).str.strip().title()
    
    st.subheader("📋 Active Workstream Schedule Audit")
    display_df = final_df.copy()
    display_df['start'] = display_df['start'].dt.strftime('%d/%m/%Y')
    display_df['end'] = display_df['end'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        display_df.rename(columns={
            "name": "Line Item / Deliverable", "start": "Start Date", "end": "End Date", "resource": "Owner/Resource", "status": "Status", "type": "WBS Classification"
        })[["Line Item / Deliverable", "WBS Classification", "Start Date", "End Date", "Owner/Resource", "Status"]], 
        use_container_width=True
    )

    # --- ADVANCED GRAPHIC ENGINE: GANTT + MILESTONE CONVERGENCE ---
    st.subheader("📈 Integrated Gantt Timeline & Milestone Dependency Tracking Graph")
    
    # Isolate tasks and sub-tasks for the classic pseudo-3D baseline bar tracks
    bars_df = final_df[final_df['type'].isin(['Task', 'Sub Task'])].copy()
    
    # Isolate milestones into separate state categories based on your business logic criteria
    milestones_all = final_df[final_df['type'] == 'Milestone'].copy()
    
    # Criteria: "Green" Status Milestones = Completed. "Amber" or "Red" = Incomplete
    completed_milestones = milestones_all[milestones_all['status'] == 'Green'].copy()
    pending_milestones = milestones_all[milestones_all['status'].isin(['Amber', 'Red'])].copy()

    # Base Palette for Gantt tracks
    gantt_palette = {
        'Task': '#2c3e50',      # Dark Charcoal Navy for prominent Top-Level Tasks
        'Sub Task': '#7f8c8d'   # Clean Steel Gray for nested supporting sub-tasks
    }
    
    # Generate background structural matrix timeline
    if not bars_df.empty:
        fig = px.timeline(
            bars_df, 
            x_start="start", 
            x_end="end", 
            y="name", 
            color="type",
            hover_data=["resource", "status"],
            color_discrete_map=gantt_palette
        )
    else:
        # Fallback if user uploads a sheet entirely composed of milestones
        fig = go.Figure()

    # 1. Overlay PENDING MILESTONES (Render as sharp Orange/Amber Triangles)
    if not pending_milestones.empty:
        fig.add_trace(
            go.Scatter(
                x=pending_milestones['start'],
                y=pending_milestones['name'],
                mode='markers',
                marker=dict(
                    symbol='triangle-up',
                    size=16,
                    color='#e67e22', # Warning Safety Amber/Orange
                    line=dict(color='#d35400', width=2)
                ),
                name='Milestone (Pending/At Risk)',
                hovertemplate="<b>%{y}</b><br>Target: %{x|%d/%m/%Y}<br>Status: Pending/Active<extra></extra>"
            )
        )

    # 2. Overlay COMPLETED MILESTONES (Render as Green Ticks/Checkmarks)
    if not completed_milestones.empty:
        fig.add_trace(
            go.Scatter(
                x=completed_milestones['start'],
                y=completed_milestones['name'],
                mode='markers',
                marker=dict(
                    symbol='line-ew-open', # Generates clean structural crossing slash lines mimicking a checklist mark
                    size=18,
                    color='#27ae60', # Vibrant Success Emerald Green
                    line=dict(color='#27ae60', width=4)
                ),
                name='Milestone (Completed Check)',
                hovertemplate="<b>%{y}</b><br>Achieved: %{x|%d/%m/%Y}<br>Status: Complete ✅<extra></extra>"
            )
        )

    # Sync and format the universal chart configuration settings
    # Extract complete ordered unique items to maintain proper list sequencing 
    y_axis_ordering = list(final_df['name'].unique())
    
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=y_axis_ordering,
        autorange="reversed" # Preserve standard layout orientation cascading downward
    )
    
    fig.update_layout(
        xaxis_title="Calendar Framework Timeline",
        yaxis_title="WBS Hierarchy Structure Items",
        legend_title="Schedule Component Legend",
        height=550,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='#f8f9fa',
        hovermode="closest"
    )
    
    # Apply structural pseudo-3D border lines to standard Gantt track traces if present
    fig.update_traces(
        marker=dict(
            line=dict(color='#2c3e50', width=1.5),
            opacity=0.9
        ),
        selector=dict(type='bar') # Target only the Gantt track blocks, avoiding scatter markers
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='#eaf0f1')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ Workstream architecture tracking engine blank. Populate fields via manual entries or document loading blocks.")
