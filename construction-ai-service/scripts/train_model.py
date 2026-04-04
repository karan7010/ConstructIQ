import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (classification_report, confusion_matrix,
                              roc_auc_score, accuracy_score)
import joblib
import os

def train_model():
    if not os.path.exists("data/training_data.csv"):
        print("Dataset not found. Run generate_dataset.py first.")
        return

    # Load data
    df = pd.read_csv("data/training_data.csv")
    X = df.drop("overrun_binary", axis=1)
    y = df["overrun_binary"]

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Model with regularisation to prevent overfitting
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_prob)
    acc = accuracy_score(y_test, y_pred)

    print("=" * 50)
    print(f"Test AUC-ROC:  {auc:.4f}")
    print(f"Test Accuracy: {acc:.4f}")
    print()
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["No Overrun", "Overrun"]))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # 5-fold cross validation for robustness check
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_aucs = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")
    print(f"\n5-Fold CV AUC: {cv_aucs.mean():.4f} (+/- {cv_aucs.std():.4f})")
    print("=" * 50)

    # Feature importance
    importance = dict(zip(X.columns, model.feature_importances_))
    # Filter out internal fields if any
    print("\nFeature Importances:")
    for feat, imp in sorted(importance.items(), key=lambda x: -x[1]):
        print(f"  {feat}: {imp:.4f}")

    # Save model
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/cost_overrun_model.pkl")
    print("\nModel saved to models/cost_overrun_model.pkl")

if __name__ == "__main__":
    train_model()
