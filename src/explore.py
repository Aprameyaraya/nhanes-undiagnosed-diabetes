"""
Week 2: exploration of the NHANES 2017-18 undiagnosed-diabetes dataset.

Run from the project root (with your .venv active):
    python src/explore.py

Reads data/merged.csv (and data/adults_all.csv if present), prints tables,
saves plots to figures/.
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

df = pd.read_csv("data/merged.csv")
os.makedirs("figures", exist_ok=True)

print("shape:", df.shape)
print("outcome prevalence:", round(df["undiagnosed"].mean(), 4), "cases:", int(df["undiagnosed"].sum()))
print("(unweighted: this describes the sample, not the US population)")


def wilson(k, n, z=1.96):
    """95% Wilson confidence interval for a proportion."""
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return centre - half, centre + half


def prevalence_by(col, title):
    rows = []
    for level, g in df.groupby(col, observed=True):
        k, n = int(g["undiagnosed"].sum()), len(g)
        lo, hi = wilson(k, n)
        rows.append({col: level, "n": n, "cases": k,
                     "prev_%": round(100 * k / n, 1),
                     "CI_low_%": round(100 * lo, 1), "CI_high_%": round(100 * hi, 1)})
    print(f"\n--- Prevalence by {title} ---")
    print(pd.DataFrame(rows).to_string(index=False))


# ---- prevalence by group (codes: see data/variables.md) ----
df["age_band"] = pd.cut(df["RIDAGEYR"], [20, 30, 40, 50, 60, 70, 81], right=False)
df["bmi_band"] = pd.cut(df["BMXBMI"], [0, 25, 30, 35, 100], right=False)
prevalence_by("age_band", "age band")
prevalence_by("RIAGENDR", "sex (RIAGENDR: 1 = male, 2 = female)")
prevalence_by("RIDRETH3", "race/ethnicity (RIDRETH3)")
prevalence_by("bmi_band", "BMI band (<25, 25-30, 30-35, 35+)")
prevalence_by("MCQ300C", "family history (MCQ300C: 1 = yes, 2 = no)")

# ---- numeric features by outcome ----
numeric = ["RIDAGEYR", "BMXBMI", "BMXWAIST", "BPXSY1", "BPXDI1", "PAD645", "PAD660"]
print("\n--- Median by outcome (0 = no, 1 = undiagnosed diabetes) ---")
print(df.groupby("undiagnosed")[numeric].median().round(1).T)

# ---- is missing blood pressure related to the outcome? ----
miss_bp = df["BPXSY1"].isna()
print("\n--- Outcome rate by whether systolic BP is missing ---")
print(df.groupby(miss_bp)["undiagnosed"].agg(["mean", "size"]).round(3))

# ---- selection check: adults missing a label vs the rest ----
if os.path.exists("data/adults_all.csv"):
    adults = pd.read_csv("data/adults_all.csv")
    no_label = adults["LBXGH"].isna() | ~adults["DIQ010"].isin([1, 2, 3])
    print("\n--- Adults with no usable label (missing HbA1c or diabetes answer) vs the rest ---")
    print("no label:", int(no_label.sum()), " has label:", int((~no_label).sum()))
    cmp = adults.assign(no_label=no_label).groupby("no_label").agg(
        n=("SEQN", "size"),
        mean_age=("RIDAGEYR", "mean"),
        pct_female=("RIAGENDR", lambda s: 100 * (s == 2).mean()),
        mean_bmi=("BMXBMI", "mean"),
    )
    print(cmp.round(1))
    print("\nRace/ethnicity mix (column %):")
    print(pd.crosstab(adults["RIDRETH3"], no_label, normalize="columns").round(3))
else:
    print("\n(data/adults_all.csv not found: add the one-line save to load.py to run the selection check)")

# ---- plots: distributions by outcome ----
for col in ["RIDAGEYR", "BMXBMI", "BMXWAIST", "BPXSY1"]:
    plt.figure(figsize=(6, 4))
    for label, g in df.groupby("undiagnosed"):
        plt.hist(g[col].dropna(), bins=30, alpha=0.5, density=True,
                 label="undiagnosed" if label == 1 else "no diabetes")
    plt.xlabel(col)
    plt.ylabel("density")
    plt.legend()
    plt.title(f"{col} by outcome")
    plt.tight_layout()
    plt.savefig(f"figures/hist_{col}.png", dpi=120)
    plt.close()

print("\nsaved plots to figures/")