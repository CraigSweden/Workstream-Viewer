import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Workstream Visualizer & Bottleneck Detector", layout="wide")

st.title("📊 Enterprise Workstream Visualizer & Automated Bottleneck Analyzer")
st.markdown("Upload your project schedule spreadsheet (using **DD/MM/YYYY** dates) to instantly map dependencies and flag risks.")

# --- SIDEBAR: DATA UPLOAD & SOURCE MANAGEMENT ---
st.sidebar.header("📁 Data Source Configuration")
upload_mode = st.sidebar.radio("Choose Input Method:", ["Upload Spreadsheet (Excel / CSV)", "Manual Live Entry"])

# Pre-baked default demo dataset showing DD/MM/YYYY format compatibility
demo_data = [
    {"name": "Market Research & Analysis", "start": "01/07/2026", "end": "12/07/2026", "resource": "Product Team"},
    {"name": "UI/UX Wireframing", "start": "10/07/2026", "end": "22/07/2026", "resource": "Design Studio"},
    {"name": "Backend Core Architecture", "start": "20/07/2026", "end": "15/08/2026", "resource": "Dev Engineering"},
    {"name": "Frontend Module Assembly", "start": "05/08/2026", "end": "01/09/2026", "resource": "Dev Engineering"},
    {"name": "System Integration Testing", "start": "05/09/2026", "end": "25/08/2026", "resource": "QA Automation"}, # Chronology Error Demo
    {"name": "User Acceptance Testing", "start": "02/09/2026", "end": "15/09/2026", "resource": "Product Team"}
]

final_df = None

if upload_mode == "Upload Spreadsheet (Excel / CSV)":
    st.sidebar.subheader("Excel / CSV Uploader")
    uploaded_file = st.sidebar.file_uploader(
        "Upload file (Columns required: Workstream Name, Start Date, End Date, Assigned Resource)", 
        type=["xlsx", "csv"]
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                raw_df = pd.read_csv(uploaded_file)
            else:
                # Read Excel file natively
                raw_df = pd.read_excel(uploaded_file)
            
            # Dynamic structural mapping to ensure standard column naming constraints
            rename_map = {
                "Workstream Name": "name", "workstream name": "name", "Workstream": "name", "name": "name",
                "Start Date": "start", "start date": "start", "Start": "start", "start": "start",
                "End Date": "end", "end date": "end", "End": "end", "end": "end",
                "Assigned Resource": "resource", "assigned resource": "resource", "Resource": "resource", "resource": "resource"
            }
            raw_df = raw_df.rename(columns=rename_map)
            
            # Check for structural compliance
            required_cols = ['name', 'start', 'end', 'resource']
            if all(col in raw_df.columns for col in required_cols):
                final_df = raw_df[required_cols].dropna(subset=['name', 'start', 'end']).copy()
                st.sidebar.success("✅ Dataset loaded successfully!")
            else:
                missing = [c for c in required_cols if c not in raw_df.columns]
                st.sidebar.error(f"❌ Structural Mismatch. Missing columns: {missing}")
        except Exception as e:
            st.sidebar.error(f"Error parsing file: {e}")
    else:
        st.info("👋 Showing default demo framework data. Drag and drop your spreadsheet into the sidebar box to test your own scheduling updates.")
        final_df = pd.DataFrame(demo_data)

else:
    # --- MANUAL ENTRY TRACKING MODE ---
    if "manual_workstreams" not in st.session_state:
        st.session_state.manual_workstreams = demo_data.copy()
        
    st.sidebar.subheader("Create New Entry")
    m_name = st.sidebar.text_input("Workstream Name", placeholder="e.g., API Deployment")
    m_res = st.sidebar.text_input("Assigned Resource / Team", placeholder="e.g., DevOps")
    m_start = st.sidebar.date_input("Start Date", datetime.today())
    m_end = st.sidebar.date_input("End Date", datetime.today())
    
    if st.sidebar.button("Add Item"):
        if m_name and m_res:
            # Save internal manual additions directly into DD/MM/YYYY format string matching the specification
            st.session_state.manual_workstreams.append({
                "name": m_name, 
                "start": m_start.strftime("%d/%m/%Y"), 
                "end": m_end.strftime("%d/%m/%Y"), 
                "resource": m_res
            })
            st.rerun()
            
    if st.button("🗑️ Clear Live Table Entries"):
        st.session_state.manual_workstreams = []
        st.rerun()
        
    final_df = pd.DataFrame(st.session_state.manual_workstreams)


# --- PROCESSING CORE PIPELINE & MATHEMATICAL ERROR FLAGS ---
if final_df is not None and not final_df.empty:
    
    # FORCE PARSING PREFERENCE: Strict DD/MM/YYYY configuration setup
    # dayfirst=True ensures pandas reads 05/08/2026 as August 5th, not May 8th.
    final_df['start'] = pd.to_datetime(final_df['start'], dayfirst=True, errors='coerce')
    final_df['end'] = pd.to_datetime(final_df['end'], dayfirst=True, errors='coerce')
    
    # Strip rows with completely unparseable or broken text entries inside date boxes
    final_df = final_df.dropna(subset=['start', 'end'])
    
    final_df['Status'] = '🟢 Clear'
    final_df['Issues/Notes'] = 'No issues detected.'

    # 1. Evaluate Logical Date Mistakes (End date preceding Start date)
    for idx, row in final_df.iterrows():
        if row['end'] < row['start']:
            final_df.at[idx, 'Status'] = '⚠️ Date Mistake'
            final_df.at[idx, 'Issues/Notes'] = f"Chronology Error: End date ({row['end'].strftime('%d/%m/%Y')}) precedes Start date ({row['start'].strftime('%d/%m/%Y')})."

    # 2. Evaluate Cascade/Resource Bottlenecks (Timeline overlaps on identical resource allocations)
    for i, row_a in final_df.iterrows():
        if final_df.at[i, 'Status'] == '⚠️ Date Mistake':
            continue
            
        for j, row_b in final_df.iterrows():
            if i != j and str(row_a['resource']).strip().lower() == str(row_b['resource']).strip().lower():
                latest_start = max(row_a['start'], row_b['start'])
                earliest_end = min(row_a['end'], row_b['end'])
                
                if latest_start <= earliest_end:
                    final_df.at[i, 'Status'] = '🔴 Bottleneck'
                    final_df.at[i, 'Issues/Notes'] = f"Resource Conflict: Double-booked with '{row_b['name']}' from {latest_start.strftime('%d/%m/%Y')} to {earliest_end.strftime('%d/%m/%Y')}."

    # --- MAIN VIEW PRESENTATION LAYOUT ---
    st.subheader("📋 Active Workstream Schedule Audit")
    
    display_df = final_df.copy()
    # Output the interactive table back to user explicitly in clean DD/MM/YYYY strings
    display_df['start'] = display_df['start'].dt.strftime('%d/%m/%Y')
    display_df['end'] = display_df['end'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        display_df.rename(columns={
            "name": "Workstream", "start": "Start Date", "end": "End Date", "resource": "Resource Assigned"
        })[["Workstream", "Start Date", "End Date", "Resource Assigned", "Status", "Issues/Notes"]], 
        use_container_width=True
    )

    # --- GRAPHIC VISUALIZATION LAYOUT ---
    st.subheader("📈 Gantt Timeline Dependency Graph")
    
    status_palette = {
        '🟢 Clear': '#2ecc71',
        '🔴 Bottleneck': '#e74c3c',
        '⚠️ Date Mistake': '#f39c12'
    }
    
    fig = px.timeline(
        final_df, 
        x_start="start", 
        x_end="end", 
        y="name", 
        color="Status",
        hover_data=["resource", "Issues/Notes"],
        color_discrete_map=status_palette,
        title="Interactive Gantt Analysis Matrix (Hover cursor blocks for error context)"
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        xaxis_title="Calendar Timeline",
        yaxis_title="Registered Project Workstreams",
        legend_title="Risk Classification Status",
        height=450,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    # Force the display popup flags on the timeline chart itself to present visually as DD/MM/YYYY
    fig.update_traces(xhoverformat="%d/%m/%Y")
    
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ Schedule tracking database empty. Upload an administrative document or toggle manually inside the sidebar to initialize visual plotting blocks.")
