import joblib
import pandas as pd
import streamlit as st

@st.cache_resource
def load_model():
    return joblib.load('cost_model.pkl')

def predict_cost(area, floors, tier, grade):
    model = load_model()
    input_data = pd.DataFrame({
        'area': [area],
        'floors': [floors],
        'tier': [tier],
        'grade': [grade]
    })
    prediction = model.predict(input_data)
    return float(prediction[0])
