"""
Load, merge and clean NHANES 2017-2018 for the undiagnosed-diabetes project.

Run from the project root (with your .venv active):
    python src/load.py

Writes data/merged.csv and prints the checks to paste back.
"""

import sys

import numpy as np
import pandas as pd

RAW = "data/raw"

FILES = {
    "demo": "DEMO_J.xpt",
    "bmx": "BMX_J.xpt",
    "bpx": "BPX_J.xpt",
    "ghb": "GHB_J.xpt",
    "diq": "DIQ_J.xpt",
    "paq": "PAQ_J.xpt",
    "mcq": "MCQ_J.xpt",
}

# Columns to keep from each file (names confirmed to exist in your data).
WANTED = {
    "demo": ["SEQN", "RIAGENDR", "RIDAGEYR", "RIDRETH3", "WTMEC2YR"],
    "bmx": ["SEQN", "BMXBMI", "BMXWAIST"],
    "bpx": ["SEQN", "BPXSY1", "BPXDI1"],
    "ghb": ["SEQN", "LBXGH"],
    "diq": ["SEQN", "DIQ010"],
    "paq": ["SEQN", "PAQ635", "PAD645", "PAQ650", "PAD660"],
    "mcq": ["SEQN", "MCQ300C"],
}


def load_files():
    dfs = {}
    for key, fname in FILES.items():
        d = pd.read_sas(f"{RAW}/{fname}", format="xport")
        if not d["SEQN"].is_unique:
            sys.exit(f"{fname}: SEQN is not unique, stopping.")
        missing = [c for c in WANTED[key] if c not in d.columns]
        if missing:
            sys.exit(f"{fname}: missing columns {missing}. Check the codebook.")
        print(f"{key:5s} rows={len(d):5d}")
        dfs[key] = d[WANTED[key]]
    return dfs


def merge(dfs):
    df = dfs["demo"]
    for key in ["bmx", "bpx", "ghb", "diq", "paq", "mcq"]:
        df = df.merge(dfs[key], on="SEQN", how="left")
    assert len(df) == len(dfs["demo"]), "merge changed the row count"
    return df


def clean(df):
    print("\nall respondents:", len(df))

    # adults only
    df = df[df["RIDAGEYR"] >= 20].copy()
    print("adults (20+):", len(df))

    # "refused" / "don't know" codes -> missing
    for c in ["DIQ010", "MCQ300C", "PAQ635", "PAQ650"]:
        df[c] = df[c].replace({7: np.nan, 9: np.nan})
    for c in ["PAD645", "PAD660"]:
        df[c] = df[c].replace({7777: np.nan, 9999: np.nan})
        # SAS XPORT stores exact zero as ~5e-79. A diastolic BP of 0 is not a real
    # pressure (likely a measurement artifact), so treat it as missing.
    n_zero_dbp = (df["BPXDI1"] < 1).sum()
    df.loc[df["BPXDI1"] < 1, "BPXDI1"] = np.nan
    print("BPXDI1 zero readings set to missing:", n_zero_dbp)

    # activity minutes are only asked if the gate question was "yes" (1).
    # Gate "no" (2) means 0 minutes; a missing gate stays missing.
    for gate, mins in [("PAQ635", "PAD645"), ("PAQ650", "PAD660")]:
        df[mins] = np.where(df[gate] == 2, 0, np.where(df[gate] == 1, df[mins], np.nan))

    # need an HbA1c value and a clear diabetes-history answer
    print("\nDIQ010 value counts (1=yes, 2=no, 3=borderline):")
    print(df["DIQ010"].value_counts(dropna=False))
    before = len(df)
    df = df.dropna(subset=["LBXGH", "DIQ010"])
    print("dropped for missing HbA1c or DIQ010:", before - len(df))

    # screening population = adults WITHOUT a known diagnosis (DIQ010 == 2).
    # Diagnosed (1) and borderline (3) are excluded, otherwise people who
    # already know they have diabetes would be wrongly labelled "negative".
    n_diag = (df["DIQ010"] == 1).sum()
    n_border = (df["DIQ010"] == 3).sum()
    df = df[df["DIQ010"] == 2].copy()
    print(f"excluded diagnosed: {n_diag}, borderline: {n_border}; remaining: {len(df)}")

    # outcome: undiagnosed diabetes by HbA1c (verify the 6.5 cutoff in the CDC docs)
    df["undiagnosed"] = (df["LBXGH"] >= 6.5).astype(int)
    return df


def main():
    dfs = load_files()
    df = merge(dfs)
    print("merged shape:", df.shape)

    df = clean(df)
    print("\nfinal shape:", df.shape)
    print("outcome prevalence:", round(df["undiagnosed"].mean(), 4))
    print("outcome counts:\n", df["undiagnosed"].value_counts())

    print("\nmissing fraction per column:")
    print(df.isna().mean().round(3).sort_values(ascending=False))

    # LBXGH defines the outcome: never use it (or DIQ010) as a model feature.
    df.to_csv("data/merged.csv", index=False)
    print("\nsaved data/merged.csv")


if __name__ == "__main__":
    main()
