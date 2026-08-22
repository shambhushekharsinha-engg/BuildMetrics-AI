content = '''import streamlit as st
import pandas as pd
import plotly.express as px
from civil_math import calculate_quantities
from cost_engine import predict_cost
from db import log_project, get_projects_log
from export import generate_boq_pdf
from blueprint_generator import generate_blueprint

st.set_page_config(page_title="BuildMetrics AI", layout="wide")

st.title("BuildMetrics AI")
st.subheader("Automated Civil Construction Cost Estimation & Quantity Modeling Engine")

# Tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["Design & Blueprint", "Cost & Estimation", "Project History"])

with tab1:
    st.header("Home Design & Blueprint Generator")
    st.write("Generate a procedural 2D spatial layout (blueprint) based on your room requirements.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Design Parameters")
        bp_area = st.number_input("Total Plot Area (sq ft)", min_value=500, max_value=10000, value=1200, step=100)
        bp_beds = st.slider("Number of Bedrooms", min_value=1, max_value=6, value=2)
        bp_baths = st.slider("Number of Bathrooms", min_value=1, max_value=4, value=2)
        
        generate_btn = st.button("Generate Blueprint")
        
    with col2:
        if generate_btn:
            fig = generate_blueprint(bp_area, bp_beds, bp_baths)
            st.pyplot(fig)
            st.success("Blueprint Generated Successfully!")
        else:
            st.info("Set your parameters and click 'Generate Blueprint' to visualize the floor plan.")

with tab2:
    st.header("Cost Estimation & BOQ")
    
    st.sidebar.header("Cost Parameters")
    area = st.sidebar.slider("Built-up Area (sq ft)", min_value=500, max_value=5000, value=1200, step=100)
    floors = st.sidebar.number_input("Number of Floors", min_value=1, max_value=10, value=1)
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
        
        col_q, col_c = st.columns(2)
        
        with col_q:
            st.write("#### Material Quantities")
            df_quantities = pd.DataFrame([
                {"Material": "Concrete", "Quantity": quantities['concrete_cum'], "Unit": "Cubic Meters"},
                {"Material": "Steel", "Quantity": quantities['steel_kg'], "Unit": "Kg"},
                {"Material": "Bricks", "Quantity": quantities['bricks'], "Unit": "Pieces"},
                {"Material": "Dry Mortar", "Quantity": quantities['dry_mortar_cum'], "Unit": "Cubic Meters"}
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
            label="Download BOQ (PDF)",
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
'''
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
