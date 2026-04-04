import pandas as pd
import numpy as np
import os

def generate_dataset(n=1000):
    np.random.seed(42)
    
    # Base features with realistic distributions
    material_deviation_avg = np.random.normal(loc=0.12, scale=0.18, size=n).clip(-0.05, 0.80)
    equipment_idle_ratio = np.random.beta(a=2, b=5, size=n)  # skewed toward lower values
    days_elapsed_pct = np.random.uniform(0.1, 0.95, size=n)
    budget_size = np.random.lognormal(mean=4.5, sigma=0.8, size=n)  # INR lakhs, skewed
    project_type = np.random.choice([0, 1, 2], size=n, p=[0.5, 0.35, 0.15])

    # Overrun probability — realistic, not deterministic
    # Multiple factors contribute with noise
    log_odds = (
        2.5 * material_deviation_avg
        + 1.8 * equipment_idle_ratio
        + 0.5 * days_elapsed_pct
        - 0.3 * (budget_size / budget_size.max())
        + 0.4 * (project_type == 2).astype(float)  # infrastructure slightly higher risk
        - 1.2                                        # intercept
        + np.random.normal(0, 0.6, size=n)          # noise term — this is KEY
    )
    probability = 1 / (1 + np.exp(-log_odds))

    # Binary target with threshold + noise
    overrun_binary = (probability > 0.5).astype(int)
    # Add ~8% label noise to simulate real-world ambiguity
    noise_mask = np.random.rand(n) < 0.08
    overrun_binary[noise_mask] = 1 - overrun_binary[noise_mask]

    df = pd.DataFrame({
        "material_deviation_avg": material_deviation_avg,
        "equipment_idle_ratio": equipment_idle_ratio,
        "days_elapsed_pct": days_elapsed_pct,
        "budget_size": budget_size,
        "project_type_encoded": project_type,
        "overrun_binary": overrun_binary
    })

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/training_data.csv", index=False)
    print(f"Dataset generated: {n} rows, {overrun_binary.mean():.1%} overrun rate")

if __name__ == "__main__":
    generate_dataset()
