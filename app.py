import streamlit as st
import pandas as pd
import plotly.express as px
from civil_math import calculate_quantities
from cost_engine import predict_cost
from db import log_project, get_projects_log
from export import generate_boq_pdf

st.set_page_config(page_title="BuildMetrics AI", layout="wide")

st.title("BuildMetrics AI")
st.subheader("Automated Civil Construction Cost Estimation & Quantity Modeling Engine")

# Input Section
st.sidebar.header("Project Parameters")
area = st.sidebar.slider("Built-up Area (sq ft)", min_value=500, max_value=5000, value=1000, step=100)
floors = st.sidebar.number_input("Number of Floors", min_value=1, max_value=10, value=1)
perimeter = st.sidebar.number_input("Perimeter (ft) [Optional]", min_value=0, value=0)
if perimeter == 0:
    perimeter = None

tier = st.sidebar.selectbox("Geographic Location/Tier", ["Tier 1", "Tier 2", "Tier 3"])
grade = st.sidebar.selectbox("Material Quality Grade", ["Standard", "Premium", "Luxury"])

if st.sidebar.button("Calculate & Estimate"):
    # 1. Civil Math
    quantities = calculate_quantities(area, perimeter, floors)
    
    # 2. ML Prediction
    estimated_cost = predict_cost(area, floors, tier, grade)
    
    # 3. Log to DB
    log_project(area, floors, tier, grade, estimated_cost)
    
    # Display Results
    st.success(f"### Total Estimated Cost: ?{estimated_cost:,.2f}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### Material Quantities")
        df_quantities = pd.DataFrame([
            {"Material": "Concrete", "Quantity": quantities['concrete_cum'], "Unit": "Cubic Meters"},
            {"Material": "Steel", "Quantity": quantities['steel_kg'], "Unit": "Kg"},
            {"Material": "Bricks", "Quantity": quantities['bricks'], "Unit": "Pieces"},
            {"Material": "Dry Mortar", "Quantity": quantities['dry_mortar_cum'], "Unit": "Cubic Meters"}
        ])
        st.dataframe(df_quantities, hide_index=True)
        
    with col2:
        st.write("#### Cost Distribution (Simulated)")
        # Just to show a chart as requested
        labels = ['Concrete', 'Steel', 'Masonry', 'Labor & Others']
        values = [estimated_cost * 0.25, estimated_cost * 0.20, estimated_cost * 0.15, estimated_cost * 0.40]
        fig = px.pie(names=labels, values=values, title="Estimated Cost Breakdown")
        st.plotly_chart(fig)
        
    # PDF Export
    pdf_buffer = generate_boq_pdf(area, floors, tier, grade, quantities, estimated_cost)
    st.download_button(
        label="Download BOQ (PDF)",
        data=pdf_buffer,
        file_name="BOQ_Report.pdf",
        mime="application/pdf"
    )

st.markdown("---")
st.write("### Project History")
history = get_projects_log()
if history:
    df_history = pd.DataFrame(history, columns=['ID', 'Timestamp', 'Area', 'Floors', 'Tier', 'Grade', 'Estimated Cost'])
    st.dataframe(df_history, hide_index=True)
else:
    st.write("No history available.")

