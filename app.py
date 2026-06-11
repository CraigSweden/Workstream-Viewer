import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

st.set_page_config(page_title="Workstream Visualizer & Milestones Engine", layout="wide")

st.title("📊 Enterprise Workstream Visualizer & Milestone Timeline Matrix")
st.markdown("Upload your hierarchy spreadsheet (**DD/MM/YYYY** dates). **Tasks** and **Sub Tasks** render as timeline tracks. **Milestones** track by *End Date* and dynamically switch to ticks upon completion!")

# --- SIDEBAR: DATA UPLOAD & SOURCE MANAGEMENT ---
st.sidebar.header("📁 Data Source Configuration")
upload_mode = st.sidebar.radio("Choose Input Method:", ["Upload Spreadsheet (Excel / CSV)", "Manual Live Entry"])

# Demo dataset showing the dynamic milestone triangle -> tick conversion logic
demo_data = [
    {"name": "1.0 Core Market Analysis Framework", "start": "01/07/2026", "end": "15/07/2026", "resource": "Product Team", "status": "Green", "type": "Task"},
    {"name": "   1.1 Competitor Benchmarking", "start": "01/07/2026", "end": "08/07/2026", "resource": "Product Team", "status": "Green", "type": "Sub Task"},
    {"name": "🚩 Past Achieved Gate (Completed)", "start": "", "end": "01/06/2026", "resource": "Product Team", "status": "Green", "type": "Milestone"}, # Status Green + Past Date = GREEN TICK
    {"name": "⭐ Future Gate (Trending Well)", "start": "", "end": "25/12/2026", "resource": "Design Studio", "status": "Green", "type": "Milestone"}, # Status Green + Future Date = GREEN TRIANGLE
    {"name": "⚠️ At Risk Future Gate", "start": "", "end": "30/08/2026", "resource": "Dev Engineering", "status": "Amber", "type": "Milestone"} # Status Amber = AMBER TRIANGLE
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
                final_df = raw_df[required_cols].dropna(subset=['name', 'end']).copy()
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
    m_name = st.sidebar.text_input("Row Name")
    m_res = st.sidebar.text_input("Assigned Team Pool", placeholder="e.g., DevOps Group")
    m_start = st.sidebar.date_input("Start Date (Leave blank for milestones)", datetime.today())
    m_end = st.sidebar.date_input("End Date / Milestone Date", datetime.today())
    m_status = st.sidebar.selectbox("Status Color Map", ["Green", "Amber", "Red"])
    m_type = st.sidebar.selectbox("Structural Classification Type", ["Task", "Sub Task", "Milestone"])
    
    if st.sidebar.button("Add Item Row"):
        if m_name and m_res:
            st.session_state.manual_workstreams.append({
                "name": m_name, 
                "start": m_start.strftime("%d/%m/%Y") if m_type != "Milestone" else "", 
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
    
    # Safely convert dates preserving DD/MM/YYYY format parsing rules
    final_df['end'] = pd.to_datetime(final_df['end'], dayfirst=True, errors='coerce')
    final_df['start'] = pd.to_datetime(final_df['start'], dayfirst=True, errors='coerce')
    
    final_df = final_df.dropna(subset=['name', 'end'])
    
    final_df['status'] = final_df['status'].astype(str).str.strip().str.capitalize()
    final_df['type'] = final_df['type'].astype(str).str.strip().str.title()
    
    st.subheader("📋 Active Workstream Schedule Audit")
    display_df = final_df.copy()
    display_df['start'] = display_df['start'].dt.strftime('%d/%m/%Y').fillna("-")
    display_df['end'] = display_df['end'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        display_df.rename(columns={
            "name": "Line Item / Deliverable", "start": "Start Date", "end": "End/Milestone Date", "resource": "Owner/Resource", "status": "Status", "type": "WBS Classification"
        })[["Line Item / Deliverable", "WBS Classification", "Start Date", "End/Milestone Date", "Owner/Resource", "Status"]], 
        use_container_width=True
    )

    # --- ADVANCED GRAPHIC ENGINE: GANTT + MILESTONE CONVERGENCE ---
    st.subheader("📈 Integrated Gantt Timeline & Milestone Dependency Tracking Graph")
    
    # 1. Separate Tasks/Sub Tasks bar tracks (Require valid start dates)
    bars_df = final_df[final_df['type'].isin(['Task', 'Sub Task'])].dropna(subset=['start']).copy()
    
    # 2. Separate Milestones (Tracked purely via End Date)
    milestones_df = final_df[final_df['type'] == 'Milestone'].copy()

    # Base Palette for Gantt tracks
    gantt_palette = {
        'Task': '#2c3e50',      # Dark Charcoal Navy
        'Sub Task': '#7f8c8d'   # Steel Gray
    }
    
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
        fig = go.Figure()

    # 3. Categorize and plot milestones dynamically based on Today's date
    if not milestones_df.empty:
        today_dt = pd.to_datetime(date.today())
        
        # Split into distinct milestone categories
        green_future = milestones_df[(milestones_df['status'] == 'Green') & (milestones_df['end'] > today_dt)]
        green_achieved = milestones_df[(milestones_df['status'] == 'Green') & (milestones_df['end'] <= today_dt)]
        amber_milestones = milestones_df[milestones_df['status'] == 'Amber']
        red_milestones = milestones_df[milestones_df['status'] == 'Red']

        # Category A: Green Future Milestones -> Render as GREEN TRIANGLE
        if not green_future.empty:
            fig.add_trace(go.Scatter(
                x=green_future['end'], y=green_future['name'], mode='markers',
                marker=dict(symbol='triangle-up', size=15, color='#27ae60', line=dict(color='#1e8449', width=1.5)),
                name='Milestone: Trending Well (Future)',
                hovertemplate="<b>%{y}</b><br>Target Date: %{x|%d/%m/%Y}<br>Status: Trending Well 🟢<extra></extra>"
            ))

        # Category B: Green Past/Present Milestones -> Render as GREEN TICK / CHECKMARK
        if not green_achieved.empty:
            fig.add_trace(go.Scatter(
                x=green_achieved['end'], y=green_achieved['name'], mode='markers',
                marker=dict(symbol='line-ew-open', size=18, color='#27ae60', line=dict(color='#27ae60', width=4)),
                name='Milestone: Completed & Achieved',
                hovertemplate="<b>%{y}</b><br>Achieved Date: %{x|%d/%m/%Y}<br>Status: Achieved ✅<extra></extra>"
            ))

        # Category C: Amber Milestones -> Render as AMBER TRIANGLE
        if not amber_milestones.empty:
            fig.add_trace(go.Scatter(
                x=amber_milestones['end'], y=amber_milestones['name'], mode='markers',
                marker=dict(symbol='triangle-up', size=15, color='#f39c12', line=dict(color='#d35400', width=1.5)),
                name='Milestone: At Risk (Amber)',
                hovertemplate="<b>%{y}</b><br>Target Date: %{x|%d/%m/%Y}<br>Status: At Risk ⚠️<extra></extra>"
            ))

        # Category D: Red Milestones -> Render as RED TRIANGLE
        if not red_milestones.empty:
            fig.add_trace(go.Scatter(
                x=red_milestones['end'], y=red_milestones['name'], mode='markers',
                marker=dict(symbol='triangle-up', size=15, color='#e74c3c', line=dict(color='#c0392b', width=1.5)),
                name='Milestone: Critical Delayed (Red)',
                hovertemplate="<b>%{y}</b><br>Target Date: %{x|%d/%m/%Y}<br>Status: Critical/Delayed 🚨<extra></extra>"
            ))

    # Clean layout controls
    y_axis_ordering = list(final_df['name'].unique())
    fig.update_yaxes(categoryorder="array", categoryarray=y_axis_ordering, autorange="reversed")
    
    fig.update_layout(
        xaxis_title="Calendar Framework Timeline",
        yaxis_title="WBS Hierarchy Structure Items",
        legend_title="Schedule Component Legend",
        height=550,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='#f8f9fa',
        hovermode="closest"
    )
    
    fig.update_traces(
        marker=dict(line=dict(color='#2c3e50', width=1.5), opacity=0.9),
        selector=dict(type='bar')
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='#eaf0f1')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ Workstream architecture tracking engine blank. Populate fields via manual entries or document loading blocks.")
