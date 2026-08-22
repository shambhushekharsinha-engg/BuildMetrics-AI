import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from civil_math import calculate_quantities
from cost_engine import predict_cost
from db import log_project, get_projects_log
from export import generate_boq_pdf
from blueprint_generator import generate_blueprint

st.set_page_config(page_title="BuildMetrics AI", layout="wide")

st.title("BuildMetrics AI")
st.subheader("Automated Civil Construction Cost Estimation & Quantity Modeling Engine")

# NLP Parser function
def parse_requirements(text):
    area_match = re.search(r'(\d+)\s*(?:sqft|sq ft|square feet)', text, re.IGNORECASE)
    bed_match = re.search(r'(\d+)\s*(?:bhk|bed|bedrooms|bedroom)', text, re.IGNORECASE)
    bath_match = re.search(r'(\d+)\s*(?:bath|bathroom|bathrooms)', text, re.IGNORECASE)
    
    parsed_area = int(area_match.group(1)) if area_match else 1200
    parsed_beds = int(bed_match.group(1)) if bed_match else 2
    parsed_baths = int(bath_match.group(1)) if bath_match else 2
    return parsed_area, parsed_beds, parsed_baths

# 3D Model Generator function
def generate_3d_model(area, floors):
    # Calculate dimensions assuming square shape
    side = (area) ** 0.5
    fig = go.Figure()
    
    floor_height = 10  # 10 ft per floor
    
    for f in range(floors):
        z_base = f * floor_height
        z_top = (f + 1) * floor_height
        
        # Define 8 corners of the floor
        x = [0, side, side, 0, 0, side, side, 0]
        y = [0, 0, side, side, 0, 0, side, side]
        z = [z_base, z_base, z_base, z_base, z_top, z_top, z_top, z_top]
        
        # define faces
        i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
        j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
        k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
        
        color = '#0055A4' if f % 2 == 0 else '#0077D4'
        
        fig.add_trace(go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=0.8, name=f'Floor {f+1}'))
        
    fig.update_layout(
        scene=dict(
            xaxis_title='Width (ft)',
            yaxis_title='Length (ft)',
            zaxis_title='Height (ft)',
            aspectmode='data'
        ),
        title="3D Building Volume Visualization",
        margin=dict(l=0, r=0, b=0, t=40)
    )
    return fig

# Tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["Design & Blueprint", "Cost & Estimation", "Project History"])

with tab1:
    st.header("Home Design & Blueprint Generator")
    
    # NLP Input
    prompt = st.text_area("Describe your requirements (e.g., 'I want a 1500 sqft house with 3 bedrooms and 2 bathrooms')", "")
    
    parsed_area = 1200
    parsed_beds = 2
    parsed_baths = 2
    
    if prompt:
        parsed_area, parsed_beds, parsed_baths = parse_requirements(prompt)
        st.success(f"Parsed Parameters -> Area: {parsed_area} sqft, Bedrooms: {parsed_beds}, Bathrooms: {parsed_baths}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Design Parameters")
        bp_area = st.number_input("Total Plot Area (sq ft)", min_value=500, max_value=10000, value=parsed_area, step=100)
        bp_beds = st.slider("Number of Bedrooms", min_value=1, max_value=6, value=parsed_beds)
        bp_baths = st.slider("Number of Bathrooms", min_value=1, max_value=4, value=parsed_baths)
        bp_floors = st.slider("Number of Floors", min_value=1, max_value=10, value=1)
        
        generate_btn = st.button("Generate Layouts")
        
    with col2:
        if generate_btn:
            st.subheader("2D Professional Blueprint")
            fig_2d = generate_blueprint(bp_area, bp_beds, bp_baths)
            st.pyplot(fig_2d)
            
            st.subheader("3D Volumetric Model")
            fig_3d = generate_3d_model(bp_area, bp_floors)
            st.plotly_chart(fig_3d, use_container_width=True)
            
        else:
            st.info("Set your parameters and click 'Generate Layouts' to visualize the floor plan and 3D model.")

with tab2:
    st.header("Cost Estimation & BOQ")
    
    st.sidebar.header("Cost Parameters")
    area = st.sidebar.slider("Built-up Area (sq ft)", min_value=500, max_value=5000, value=1200, step=100)
    floors = st.sidebar.number_input("Number of Floors (Cost)", min_value=1, max_value=10, value=1)
    perimeter = st.sidebar.number_input("Perimeter (ft) [Optional]", min_value=0, value=0)
    if perimeter == 0:
        perimeter = None

    tier = st.sidebar.selectbox("Geographic Location/Tier", ["Tier 1", "Tier 2", "Tier 3"])
    grade = st.sidebar.selectbox("Material Quality Grade", ["Standard", "Premium", "Luxury"])

    if st.button("Calculate & Estimate"):
        # 1. Civil Math
        quantities = calculate_quantities(area, perimeter, floors)
        
        # 2. ML Prediction
        estimated_cost = predict_cost(area, floors, tier, grade)
        
        # 3. Log to DB
        log_project(area, floors, tier, grade, estimated_cost)
        
        # Display Results
        st.success(f"### Total Estimated Cost: ?{estimated_cost:,.2f}")
        st.info(f"Estimated Construction Duration: {quantities['estimated_days']} Days")
        
        col_q, col_c = st.columns(2)
        
        with col_q:
            st.write("#### Material & Labor Quantities")
            df_quantities = pd.DataFrame([
                {"Resource": "Concrete", "Quantity": quantities['concrete_cum'], "Unit": "Cubic Meters"},
                {"Resource": "Steel", "Quantity": quantities['steel_kg'], "Unit": "Kg"},
                {"Resource": "Bricks", "Quantity": quantities['bricks'], "Unit": "Pieces"},
                {"Resource": "Dry Mortar", "Quantity": quantities['dry_mortar_cum'], "Unit": "Cubic Meters"},
                {"Resource": "Labor", "Quantity": quantities['total_mandays'], "Unit": "Man-Days"}
            ])
            st.dataframe(df_quantities, hide_index=True)
            
        with col_c:
            st.write("#### Cost Distribution")
            labels = ['Concrete', 'Steel', 'Masonry', 'Labor & Others']
            values = [estimated_cost * 0.25, estimated_cost * 0.20, estimated_cost * 0.15, estimated_cost * 0.40]
            fig_pie = px.pie(names=labels, values=values, title="Estimated Cost Breakdown")
            st.plotly_chart(fig_pie)
            
        # PDF Export
        pdf_buffer = generate_boq_pdf(area, floors, tier, grade, quantities, estimated_cost)
        st.download_button(
            label="Download Detailed BOQ (PDF)",
            data=pdf_buffer,
            file_name="BOQ_Report.pdf",
            mime="application/pdf"
        )

with tab3:
    st.header("Project History")
    history = get_projects_log()
    if history:
        df_history = pd.DataFrame(history, columns=['ID', 'Timestamp', 'Area', 'Floors', 'Tier', 'Grade', 'Estimated Cost'])
        st.dataframe(df_history, hide_index=True)
    else:
        st.write("No history available.")
