import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

st.set_page_config(page_title="Hierarchical Workstream Matrix", layout="wide")

st.title("📊 Enterprise Hierarchical Workstream & Milestone Matrix")
st.markdown("Upload your structured schedule spreadsheet (**DD/MM/YYYY**). Sub Tasks sit under their Parent Tasks, and **Milestones are plotted directly on top of the task timeline lines**.")

# --- SIDEBAR: DATA UPLOAD & SOURCE MANAGEMENT ---
st.sidebar.header("📁 Data Source Configuration")
upload_mode = st.sidebar.radio("Choose Input Method:", ["Upload Spreadsheet (Excel / CSV)", "Manual Live Entry"])

# Demo dataset reflecting structural mapping hierarchy
demo_data = [
    {"name": "1.0 Core Architecture Framework", "start": "01/07/2026", "end": "30/07/2026", "resource": "Product Team", "status": "Green", "type": "Task", "parent": ""},
    {"name": "   1.1 Competitor Benchmarking", "start": "01/07/2026", "end": "12/07/2026", "resource": "Product Team", "status": "Green", "type": "Sub Task", "parent": "1.0 Core Architecture Framework"},
    {"name": "   1.2 User Persona Survey Pool", "start": "10/07/2026", "end": "28/07/2026", "resource": "Design Studio", "status": "Amber", "type": "Sub Task", "parent": "1.0 Core Architecture Framework"},
    {"name": "⭐ Phase 1 Strategy Sign-Off Gate", "start": "", "end": "15/07/2026", "resource": "Product Team", "status": "Green", "type": "Milestone", "parent": "1.0 Core Architecture Framework"}, # Plots directly on "1.0 Core Architecture Framework"
    
    {"name": "2.0 Database Core Implementation", "start": "15/07/2026", "end": "15/08/2026", "resource": "Dev Engineering", "status": "Amber", "type": "Task", "parent": ""},
    {"name": "   2.1 Schema Definition & Mapping", "start": "15/07/2026", "end": "02/08/2026", "resource": "Dev Engineering", "status": "Green", "type": "Sub Task", "parent": "2.0 Database Core Implementation"},
    {"name": "🚩 Security Audit Clearance Review", "start": "", "end": "20/07/2026", "resource": "QA Automation", "status": "Green", "type": "Milestone", "parent": "2.0 Database Core Implementation"} # Achieved milestone on parent line
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
    
    st.subheader("📋 Active Workstream Schedule Audit")
    display_df = final_df.copy()
    display_df['start'] = display_df['start'].dt.strftime('%d/%m/%Y').fillna("-")
    display_df['end'] = display_df['end'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        display_df.rename(columns={
            "name": "Line Item / Deliverable", "start": "Start Date", "end": "End Date", "resource": "Owner/Resource", "status": "Status", "type": "Classification", "parent": "Parent Link"
        })[["Line Item / Deliverable", "Classification", "Parent Link", "Start Date", "End Date", "Owner/Resource", "Status"]], 
        use_container_width=True
    )

    # --- GRAPHIC ENGINE: HIERARCHY MATRIX ---
    st.subheader("📈 Gantt Timeline & Inline Milestone Dependency Graph")
    
    # 1. Separate visible Timeline Bars (Tasks & Sub Tasks)
    bars_df = final_df[final_df['type'].isin(['Task', 'Sub Task'])].dropna(subset=['start']).copy()
    
    # 2. Separate Milestones
    milestones_df = final_df[final_df['type'] == 'Milestone'].copy()

    # Define color scheme for Timeline bars
    gantt_palette = {
        'Task': '#2c3e50',      # Executive Charcoal Navy
        'Sub Task': '#95a5a6'   # Soft Steel Gray for nested sub-tasks
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

    # 3. Dynamic Inline Milestones Layer
    if not milestones_df.empty:
        today_dt = pd.to_datetime(date.today())
        
        # Rule: If milestone has a valid Parent Task, map it to that parent line row!
        # If no parent task is written, fall back to its own name line.
        milestones_df['y_axis_target'] = milestones_df.apply(
            lambda r: r['parent'] if (r['parent'] != "" and r['parent'] != "nan") else r['name'], axis=1
        )
        
        # Split milestones for conditional formatting
        green_future = milestones_df[(milestones_df['status'] == 'Green') & (milestones_df['end'] > today_dt)]
        green_achieved = milestones_df[(milestones_df['status'] == 'Green') & (milestones_df['end'] <= today_dt)]
        amber_milestones = milestones_df[milestones_df['status'] == 'Amber']
        red_milestones = milestones_df[milestones_df['status'] == 'Red']

        # Category A: Green Future -> GREEN TRIANGLE
        if not green_future.empty:
            fig.add_trace(go.Scatter(
                x=green_future['end'], y=green_future['y_axis_target'], mode='markers',
                marker=dict(symbol='triangle-up', size=16, color='#27ae60', line=dict(color='#1e8449', width=1.5)),
                name='Milestone: Trending Well (Future Triangle)',
                text=green_future['name'],
                hovertemplate="<b>Milestone: %{text}</b><br>Target Date: %{x|%d/%m/%Y}<br>Plotted on Track: %{y}<extra></extra>"
            ))

        # Category B: Green Past/Present -> GREEN TICK
        if not green_achieved.empty:
            fig.add_trace(go.Scatter(
                x=green_achieved['end'], y=green_achieved['y_axis_target'], mode='markers',
                marker=dict(symbol='line-ew-open', size=20, color='#27ae60', line=dict(color='#27ae60', width=4.5)),
                name='Milestone: Achieved (Tick ✅)',
                text=green_achieved['name'],
                hovertemplate="<b>Milestone: %{text}</b><br>Achieved Date: %{x|%d/%m/%Y}<br>Plotted on Track: %{y}<extra></extra>"
            ))

        # Category C: Amber -> AMBER TRIANGLE
        if not amber_milestones.empty:
            fig.add_trace(go.Scatter(
                x=amber_milestones['end'], y=amber_milestones['y_axis_target'], mode='markers',
                marker=dict(symbol='triangle-up', size=16, color='#f39c12', line=dict(color='#d35400', width=1.5)),
                name='Milestone: At Risk (Amber)',
                text=amber_milestones['name'],
                hovertemplate="<b>Milestone: %{text}</b><br>Target Date: %{x|%d/%m/%Y}<br>Plotted on Track: %{y}<extra></extra>"
            ))

        # Category D: Red -> RED TRIANGLE
        if not red_milestones.empty:
            fig.add_trace(go.Scatter(
                x=red_milestones['end'], y=red_milestones['y_axis_target'], mode='markers',
                marker=dict(symbol='triangle-up', size=16, color='#e74c3c', line=dict(color='#c0392b', width=1.5)),
                name='Milestone: Delayed (Red)',
                text=red_milestones['name'],
                hovertemplate="<b>Milestone: %{text}</b><br>Target Date: %{x|%d/%m/%Y}<br>Plotted on Track: %{y}<extra></extra>"
            ))

    # --- ADVANCED AXIS ORDERING SYSTEM ---
    # Group sub-tasks logically under their main parent tasks
    ordered_y_axis = []
    main_tasks = final_df[final_df['type'] == 'Task']['name'].unique()
    
    for task in main_tasks:
        ordered_y_axis.append(task)
        # Find all subtasks linked to this parent task
        subtasks = final_df[(final_df['type'] == 'Sub Task') & (final_df['parent'] == task)]['name'].unique()
        ordered_y_axis.extend(subtasks)
        
    # Pick up any loose items that weren't caught in the hierarchy loops
    for item in final_df['name'].unique():
        if item not in ordered_y_axis and final_df[final_df['name'] == item]['type'].values[0] != 'Milestone':
            ordered_y_axis.append(item)

    fig.update_yaxes(categoryorder="array", categoryarray=ordered_y_axis, autorange="reversed")
    
    fig.update_layout(
        xaxis_title="Calendar Framework Timeline",
        yaxis_title="Logical WBS Hierarchy",
        legend_title="Schedule Components",
        height=550,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='#f8f9fa',
        hovermode="closest"
    )
    
    fig.update_traces(
        marker=dict(line=dict(color='#2c3e50', width=1.5), opacity=0.85),
        selector=dict(type='bar')
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='#eaf0f1')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ Workstream database empty. Upload an Excel file containing a Parent Task column to render hierarchy.")
