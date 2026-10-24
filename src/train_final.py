"""
Fit the primary model (Model 3: age, BMI, family history, systolic BP)
on all clean data and save the pipeline artifact for inference.

Run from the project root:
    python src/train_final.py
"""

import os
import sys
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def main():
    # Ensure models directory exists
    os.makedirs("models", exist_ok=True)

    # Locate merged data file (handles root or data/ folder)
    csv_path = "data/merged.csv" if os.path.exists("data/merged.csv") else "merged.csv"
    if not os.path.exists(csv_path):
        print(f"Error: Could not find merged dataset at '{csv_path}'.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    y = df["undiagnosed"].astype(int)

    # Derive binary family history feature
    df["family_history"] = df["MCQ300C"].map({1.0: 1.0, 2.0: 0.0})

    # Define Model 3 pipeline
    features_num = ["RIDAGEYR", "BMXBMI", "BPXSY1"]
    features_bin = ["family_history"]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    [
                        ("imp", SimpleImputer(strategy="median", add_indicator=True)),
                        ("sc", StandardScaler()),
                    ]
                ),
                features_num,
            ),
            (
                "bin",
                SimpleImputer(strategy="most_frequent"),
                features_bin,
            ),
        ]
    )

    pipeline = Pipeline(
        [
            ("pre", preprocessor),
            ("clf", LogisticRegression(C=1.0, max_iter=2000)),
        ]
    )

    # Fit on complete dataset
    pipeline.fit(df, y)

    # Save serialized model artifact
    model_path = "models/undiagnosed_diabetes_model3.pkl"
    joblib.dump(pipeline, model_path)
    print(f"Successfully trained model on {len(df)} samples and saved to '{model_path}'.")

if __name__ == "__main__":
    main()