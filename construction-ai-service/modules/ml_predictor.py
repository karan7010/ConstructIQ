import joblib
import pandas as pd
import os

MODEL_PATH = "models/cost_overrun_model.pkl"

def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None

def predict_overrun(data: dict) -> float:
    model = load_model()
    if not model:
        return 0.0
    
    # Input data keys: material_deviation_avg, equipment_idle_ratio, days_elapsed_pct, budget_size, project_type_encoded
    df = pd.DataFrame([data])
    probability = model.predict_proba(df)[:, 1][0]
    return float(probability)
