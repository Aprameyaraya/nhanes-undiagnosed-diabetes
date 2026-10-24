"""
CLI tool to predict undiagnosed diabetes risk for an individual patient
using the trained Model 3 pipeline.

Usage:
    python predict.py --age 58 --bmi 32.1 --sys_bp 134 --family_history 1
"""

import argparse
import os
import sys
import joblib
import pandas as pd

# Import train main function directly so we don't rely on fragile CLI sub-processes
try:
    from src.train_final import main as train_model
except ImportError:
    train_model = None

MODEL_PATH = "models/undiagnosed_diabetes_model3.pkl"

def main():
    parser = argparse.ArgumentParser(
        description="Estimate undiagnosed diabetes risk using NHANES Model 3."
    )
    parser.add_argument("--age", type=float, required=True, help="Age in years (e.g., 52)")
    parser.add_argument("--bmi", type=float, required=True, help="Body Mass Index in kg/m^2 (e.g., 29.5)")
    parser.add_argument("--sys_bp", type=float, required=True, help="Systolic Blood Pressure in mm Hg (e.g., 128)")
    parser.add_argument(
        "--family_history",
        type=int,
        choices=[0, 1],
        required=True,
        help="Family history of diabetes in close relative (1 = Yes, 0 = No)",
    )

    args = parser.parse_args()

    if not os.path.exists(MODEL_PATH):
        print(f"Model file '{MODEL_PATH}' not found. Training model now...")
        if train_model is not None:
            train_model()
        else:
            sys.exit("Error: Could not import train_final.py from src/ to train the model.")

    if not os.path.exists(MODEL_PATH):
        sys.exit("Error: Model training failed or file is still missing.")

    # Load model
    model = joblib.load(MODEL_PATH)

    # Format input into a single-row DataFrame
    input_data = pd.DataFrame(
        [{
            "RIDAGEYR": args.age,
            "BMXBMI": args.bmi,
            "BPXSY1": args.sys_bp,
            "family_history": float(args.family_history),
        }]
    )

    # Predict risk score
    risk_prob = model.predict_proba(input_data)[0, 1]
    risk_pct = risk_prob * 100

    print("\n" + "=" * 55)
    print("      UNDIAGNOSED DIABETES RISK ASSESSMENT      ")
    print("=" * 55)
    print(f" Patient Parameters:")
    print(f"  - Age:                     {args.age:.0f} years")
    print(f"  - BMI:                     {args.bmi:.1f} kg/m²")
    print(f"  - Systolic BP:             {args.sys_bp:.0f} mm Hg")
    print(f"  - Family History:          {'Yes' if args.family_history == 1 else 'No'}")
    print("-" * 55)
    print(f" Estimated Undiagnosed Risk: {risk_pct:.2f}%")

    if risk_pct >= 5.28:
        print(" Recommendation: HIGH RISK (Above population 80th percentile)")
        print(" -> HbA1c or fasting plasma glucose testing recommended.")
    else:
        print(" Recommendation: LOW TO MODERATE RISK")
        print(" -> Routine clinical monitoring recommended.")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    main()