"""
Week 3: baseline and candidate models for undiagnosed diabetes (NHANES 2017-18).

Run from the project root (with your .venv active):
    python src/model.py

What it does
  1. Builds features from data/merged.csv (nothing derived from HbA1c or diagnosis).
  2. Compares a few models with repeated stratified 5-fold cross-validation.
     All preprocessing (imputation, scaling) is inside the pipeline, so it is
     fit on training folds only. No leakage.
  3. Saves out-of-fold predictions to data/oof_predictions.csv (used in week 4
     for calibration and subgroup checks).

Hyperparameters are fixed on purpose. With only 150 cases, heavy tuning on the same
data would make the results look better than they are.
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    RepeatedStratifiedKFold,
    StratifiedKFold,
    cross_val_predict,
    cross_validate,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42

# ----------------------------------------------------------------------------------
# Data and features
# ----------------------------------------------------------------------------------
df = pd.read_csv("data/merged.csv")
y = df["undiagnosed"].astype(int)

df["female"] = (df["RIAGENDR"] == 2).astype(float)
df["family_history"] = df["MCQ300C"].map({1.0: 1.0, 2.0: 0.0})  # 7/9 are already missing
df["walk_log"] = np.log1p(df["PAD645"])        # minutes per week are very skewed
df["vigorous_log"] = np.log1p(df["PAD660"])

NUM_ALL = ["RIDAGEYR", "BMXBMI", "BMXWAIST", "BPXSY1", "BPXDI1", "walk_log", "vigorous_log"]
BIN_ALL = ["female", "family_history"]
RACE = ["RIDRETH3"]

# Guard against leakage: none of these may be used as a feature.
FORBIDDEN = {"LBXGH", "DIQ010", "undiagnosed", "SEQN", "WTMEC2YR"}
used = set(NUM_ALL + BIN_ALL + RACE)
assert not (used & FORBIDDEN), f"leakage: {used & FORBIDDEN}"

print("rows:", len(df), "cases:", int(y.sum()), "prevalence:", round(y.mean(), 4))


def preprocessor(num, binary, cat, impute=True):
    parts = []
    if num:
        if impute:
            steps = [("imp", SimpleImputer(strategy="median", add_indicator=True)),
                     ("sc", StandardScaler())]
            parts.append(("num", Pipeline(steps), num))
        else:
            parts.append(("num", "passthrough", num))
    if binary:
        if impute:
            parts.append(("bin", SimpleImputer(strategy="most_frequent"), binary))
        else:
            parts.append(("bin", "passthrough", binary))
    if cat:
        parts.append(("cat", OneHotEncoder(handle_unknown="ignore"), cat))
    return ColumnTransformer(parts)


def logreg():
    # No class_weight: reweighting would distort the predicted probabilities,
    # and calibration matters for a screening model.
    return LogisticRegression(C=1.0, max_iter=2000)


def gboost():
    return HistGradientBoostingClassifier(
        learning_rate=0.05, max_iter=150, max_depth=3,
        min_samples_leaf=40, l2_regularization=1.0, random_state=RANDOM_STATE,
    )


models = {
    "0 prevalence only (dummy)": Pipeline([
        ("pre", preprocessor(["RIDAGEYR"], [], [])),
        ("clf", DummyClassifier(strategy="prior"))]),
    "1 age only (logistic)": Pipeline([
        ("pre", preprocessor(["RIDAGEYR"], [], [])), ("clf", logreg())]),
    "2 age + BMI (logistic)": Pipeline([
        ("pre", preprocessor(["RIDAGEYR", "BMXBMI"], [], [])), ("clf", logreg())]),
    "3 simple: age, BMI, family history, systolic BP (logistic)": Pipeline([
        ("pre", preprocessor(["RIDAGEYR", "BMXBMI", "BPXSY1"], ["family_history"], [])),
        ("clf", logreg())]),
    "4 all features, no race (logistic)": Pipeline([
        ("pre", preprocessor(NUM_ALL, BIN_ALL, [])), ("clf", logreg())]),
    "5 all features + race (logistic)": Pipeline([
        ("pre", preprocessor(NUM_ALL, BIN_ALL, RACE)), ("clf", logreg())]),
    "6 all features + race (gradient boosting)": Pipeline([
        ("pre", preprocessor(NUM_ALL, BIN_ALL, RACE, impute=False)), ("clf", gboost())]),
}

# ----------------------------------------------------------------------------------
# Repeated cross-validation
# ----------------------------------------------------------------------------------
cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=RANDOM_STATE)
scoring = {
    "roc_auc": "roc_auc",
    "avg_precision": "average_precision",
    "brier": "neg_brier_score",
    "log_loss": "neg_log_loss",
}

rows = []
for name, model in models.items():
    res = cross_validate(model, df, y, cv=cv, scoring=scoring, n_jobs=1)
    rows.append({
        "model": name,
        "AUROC": res["test_roc_auc"].mean(),
        "AUROC_sd": res["test_roc_auc"].std(),
        "avg_precision": res["test_avg_precision"].mean(),
        "brier": -res["test_brier"].mean(),
        "log_loss": -res["test_log_loss"].mean(),
    })
    print("done:", name)

summary = pd.DataFrame(rows)
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 70)
print("\n=== 5-fold x 5-repeat cross-validation (mean over 25 folds) ===")
print(summary.round(4).to_string(index=False))
print("\nReference values for a model with no information:")
print("  AUROC = 0.5, average precision ~", round(y.mean(), 3),
      ", Brier ~", round(y.mean() * (1 - y.mean()), 4))
print("AUROC_sd is the spread across folds, not a confidence interval.")

# ----------------------------------------------------------------------------------
# Out-of-fold predictions (for week 4: calibration and subgroup checks)
# ----------------------------------------------------------------------------------
oof = df[["SEQN", "undiagnosed", "RIDAGEYR", "RIAGENDR", "RIDRETH3"]].copy()
skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=RANDOM_STATE)
for name, model in models.items():
    p = cross_val_predict(model, df, y, cv=skf, method="predict_proba")[:, 1]
    oof[name.split(" ")[0] + "_" + name.split("(")[-1].rstrip(")").replace(" ", "_")] = p
oof.to_csv("data/oof_predictions.csv", index=False)
print("\nsaved data/oof_predictions.csv")

# ----------------------------------------------------------------------------------
# Coefficients of the full logistic model (for interpretation only, not evaluation)
# ----------------------------------------------------------------------------------
full = models["5 all features + race (logistic)"].fit(df, y)
try:
    names = full.named_steps["pre"].get_feature_names_out()
    coefs = pd.Series(full.named_steps["clf"].coef_[0], index=names)
    print("\n=== Full logistic model, standardized coefficients (log-odds per 1 SD) ===")
    print(coefs.sort_values(key=np.abs, ascending=False).round(3).to_string())
except Exception as e:  # feature names differ across scikit-learn versions
    print("could not print coefficient names:", e)
