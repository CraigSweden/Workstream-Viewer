import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Workstream Visualizer & Bottleneck Detector", layout="wide")

st.title("📊 Enterprise Workstream Visualizer & Automated Bottleneck Analyzer")
st.markdown("Upload your project schedule spreadsheet (using **DD/MM/YYYY** dates) to instantly map dependencies and apply custom status color codes.")

# --- SIDEBAR: DATA UPLOAD & SOURCE MANAGEMENT ---
st.sidebar.header("📁 Data Source Configuration")
upload_mode = st.sidebar.radio("Choose Input Method:", ["Upload Spreadsheet (Excel / CSV)", "Manual Live Entry"])

# Pre-baked default demo dataset showing DD/MM/YYYY format compatibility and custom colors
demo_data = [
    {"name": "Market Research & Analysis", "start": "01/07/2026", "end": "12/07/2026", "resource": "Product Team", "status": "Green"},
    {"name": "UI/UX Wireframing", "start": "10/07/2026", "end": "22/07/2026", "resource": "Design Studio", "status": "Green"},
    {"name": "Backend Core Architecture", "start": "20/07/2026", "end": "15/08/2026", "resource": "Dev Engineering", "status": "Red"},
    {"name": "Frontend Module Assembly", "start": "05/08/2026", "end": "01/09/2026", "resource": "Dev Engineering", "status": "Amber"},
    {"name": "System Integration Testing", "start": "02/09/2026", "end": "25/09/2026", "resource": "QA Automation", "status": "Amber"}, 
    {"name": "User Acceptance Testing", "start": "26/09/2026", "end": "15/10/2026", "resource": "Product Team", "status": "Green"}
]

final_df = None

if upload_mode == "Upload Spreadsheet (Excel / CSV)":
    st.sidebar.subheader("Excel / CSV Uploader")
    uploaded_file = st.sidebar.file_uploader(
        "Upload file (Columns required: Workstream Name, Start Date, End Date, Assigned Resource, Status)", 
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
                "Status": "status", "status": "status", "STATUS": "status"
            }
            raw_df = raw_df.rename(columns=rename_map)
            
            required_cols = ['name', 'start', 'end', 'resource', 'status']
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
    if "manual_workstreams" not in st.session_state:
        st.session_state.manual_workstreams = demo_data.copy()
        
    st.sidebar.subheader("Create New Entry")
    m_name = st.sidebar.text_input("Workstream Name", placeholder="e.g., API Deployment")
    m_res = st.sidebar.text_input("Assigned Resource / Team", placeholder="e.g., DevOps")
    m_start = st.sidebar.date_input("Start Date", datetime.today())
    m_end = st.sidebar.date_input("End Date", datetime.today())
    m_status = st.sidebar.selectbox("Status Color", ["Green", "Amber", "Red"])
    
    if st.sidebar.button("Add Item"):
        if m_name and m_res:
            st.session_state.manual_workstreams.append({
                "name": m_name, 
                "start": m_start.strftime("%d/%m/%Y"), 
                "end": m_end.strftime("%d/%m/%Y"), 
                "resource": m_res,
                "status": m_status
            })
            st.rerun()
            
    if st.button("🗑️ Clear Live Table Entries"):
        st.session_state.manual_workstreams = []
        st.rerun()
        
    final_df = pd.DataFrame(st.session_state.manual_workstreams)


if final_df is not None and not final_df.empty:
    
    final_df['start'] = pd.to_datetime(final_df['start'], dayfirst=True, errors='coerce')
    final_df['end'] = pd.to_datetime(final_df['end'], dayfirst=True, errors='coerce')
    final_df = final_df.dropna(subset=['start', 'end'])
    final_df['status'] = final_df['status'].astype(str).str.strip().str.capitalize()
    
    final_df['System Notes'] = 'Row OK'
    for idx, row in final_df.iterrows():
        if row['end'] < row['start']:
            final_df.at[idx, 'System Notes'] = f"⚠️ Chronology Error: End date precedes Start date."

    st.subheader("📋 Active Workstream Schedule Audit")
    
    display_df = final_df.copy()
    display_df['start'] = display_df['start'].dt.strftime('%d/%m/%Y')
    display_df['end'] = display_df['end'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        display_df.rename(columns={
            "name": "Workstream", "start": "Start Date", "end": "End Date", "resource": "Resource Assigned", "status": "Excel Status"
        })[["Workstream", "Start Date", "End Date", "Resource Assigned", "Excel Status", "System Notes"]], 
        use_container_width=True
    )

    # --- GRAPHIC VISUALIZATION LAYOUT ---
    st.subheader("📈 Gantt Timeline Dependency Graph")
    
    # Premium high-contrast color scheme tailored for clean text readability
    excel_status_palette = {
        'Green': '#27ae60',   # Rich Emerald
        'Amber': '#f39c12',   # Vivid Amber
        'Red': '#c0392b'      # Deep Crimson
    }
    
    fig = px.timeline(
        final_df, 
        x_start="start", 
        x_end="end", 
        y="name", 
        color="status",
        hover_data=["resource", "System Notes"],
        color_discrete_map=excel_status_palette,
        title="Interactive Gantt Chart (Colored by Excel Status Column)"
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        xaxis_title="Calendar Timeline",
        yaxis_title="Registered Project Workstreams",
        legend_title="Excel Status Override",
        height=450,
        margin=dict(l=20, r=20, t=40, b=20),
        # Light gray canvas gridlines to bounce light off the shapes
        plot_bgcolor='#f8f9fa'
    )
    
    # --- STYLING ENGINE FOR THE 3D GLASS FLOATING LOOK ---
    fig.update_traces(
        xhoverformat="%d/%m/%Y",
        marker=dict(
            line=dict(
                color='#34495e', # Crisp Charcoal structural border around every single bar
                width=2          # Generates a deliberate shadow separation effect
            ),
            opacity=0.92         # Subtle translucency simulation
        ),
        insidetextanchor="middle"
    )
    
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ Schedule tracking database empty. Upload an administrative document or toggle manually inside the sidebar to initialize visual plotting blocks.")
