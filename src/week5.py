"""
Week 5: three planned checks on the simple model.

  3a  curved age effect (age + age squared)
  3b  waist instead of BMI
  3c  both changes together
  5   the model WITH race, only to see whether it fixes the group calibration gaps

Run from the project root (with your .venv active):
    python src/week5.py

Same data, same 10 folds (random_state=42) as model.py, so model 3 and model 5 here
reproduce the earlier out-of-fold predictions. Only these planned variants are tried,
to avoid picking whatever happens to look best on 150 cases.
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42
N_BOOT = 1000
rng = np.random.default_rng(RANDOM_STATE)
os.makedirs("figures", exist_ok=True)

# ---------------------------------------------------------------- data and features
df = pd.read_csv("data/merged.csv")
y = df["undiagnosed"].astype(int).to_numpy()
n = len(df)

df["female"] = (df["RIAGENDR"] == 2).astype(float)
df["family_history"] = df["MCQ300C"].map({1.0: 1.0, 2.0: 0.0})
df["walk_log"] = np.log1p(df["PAD645"])
df["vigorous_log"] = np.log1p(df["PAD660"])
df["age_sq"] = df["RIDAGEYR"] ** 2

NUM_ALL = ["RIDAGEYR", "BMXBMI", "BMXWAIST", "BPXSY1", "BPXDI1", "walk_log", "vigorous_log"]
BIN_ALL = ["female", "family_history"]
RACE = ["RIDRETH3"]

FORBIDDEN = {"LBXGH", "DIQ010", "undiagnosed", "SEQN", "WTMEC2YR"}


def make_model(num, binary, cat):
    assert not (set(num + binary + cat) & FORBIDDEN), "leakage"
    parts = [("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                               ("sc", StandardScaler())]), num)]
    if binary:
        parts.append(("bin", SimpleImputer(strategy="most_frequent"), binary))
    if cat:
        parts.append(("cat", OneHotEncoder(handle_unknown="ignore"), cat))
    return Pipeline([("pre", ColumnTransformer(parts)),
                     ("clf", LogisticRegression(C=1.0, max_iter=2000))])


models = {
    "3 simple": make_model(["RIDAGEYR", "BMXBMI", "BPXSY1"], ["family_history"], []),
    "3a curved age": make_model(["RIDAGEYR", "age_sq", "BMXBMI", "BPXSY1"], ["family_history"], []),
    "3b waist for BMI": make_model(["RIDAGEYR", "BMXWAIST", "BPXSY1"], ["family_history"], []),
    "3c curved age + waist": make_model(["RIDAGEYR", "age_sq", "BMXWAIST", "BPXSY1"], ["family_history"], []),
    "5 with race (comparison)": make_model(NUM_ALL, BIN_ALL, RACE),
}
BASE = "3 simple"

# ---------------------------------------------------------------- out-of-fold predictions
skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=RANDOM_STATE)
oof = {}
for name, model in models.items():
    oof[name] = cross_val_predict(model, df, y, cv=skf, method="predict_proba")[:, 1]
    print("done:", name)

out = df[["SEQN", "undiagnosed", "RIDAGEYR", "RIAGENDR", "RIDRETH3"]].copy()
for name, p in oof.items():
    out[name] = p
out.to_csv("data/oof_week5.csv", index=False)

# ---------------------------------------------------------------- helpers
boot_idx = [i for i in (rng.integers(0, n, n) for _ in range(N_BOOT)) if y[i].min() != y[i].max()]


def boot_auc(p):
    return np.array([roc_auc_score(y[i], p[i]) for i in boot_idx])


def wilson(k, m, z=1.96):
    p = k / m
    denom = 1 + z**2 / m
    centre = (p + z**2 / (2 * m)) / denom
    half = z * np.sqrt(p * (1 - p) / m + z**2 / (4 * m**2)) / denom
    return centre - half, centre + half


def cal_slope(p):
    pc = np.clip(p, 1e-6, 1 - 1e-6)
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(np.log(pc / (1 - pc)).reshape(-1, 1), y)
    return lr.coef_[0, 0]


# ---------------------------------------------------------------- 1. overall comparison
print("\n=== 1. Overall comparison (out-of-fold) ===")
aucs = {name: boot_auc(p) for name, p in oof.items()}
rows = []
for name, p in oof.items():
    lo, hi = np.percentile(aucs[name], [2.5, 97.5])
    row = {"model": name,
           "AUROC (95% CI)": f"{roc_auc_score(y, p):.3f} ({lo:.3f} to {hi:.3f})",
           "log_loss": round(log_loss(y, p), 4),
           "brier": round(brier_score_loss(y, p), 4),
           "cal_slope": round(cal_slope(p), 2)}
    if name != BASE:
        d = aucs[name] - aucs[BASE]
        dlo, dhi = np.percentile(d, [2.5, 97.5])
        row["AUROC minus model 3"] = f"{d.mean():+.3f} ({dlo:+.3f} to {dhi:+.3f})"
    else:
        row["AUROC minus model 3"] = "-"
    rows.append(row)
pd.set_option("display.width", 220)
print(pd.DataFrame(rows).to_string(index=False))
print("If a paired interval includes 0, the change is unclear.")

# ---------------------------------------------------------------- 2. calibration by age band
print("\n=== 2. Observed / expected cases by age band (1.0 is ideal) ===")
bands = pd.cut(df["RIDAGEYR"], [20, 30, 40, 50, 60, 70, 81], right=False).astype(str)
rows = []
for b in sorted(bands.unique()):
    m = (bands == b).to_numpy()
    row = {"age band": b, "n": int(m.sum()), "cases": int(y[m].sum()),
           "observed_%": round(100 * y[m].mean(), 2)}
    for name, p in oof.items():
        row[name] = round(y[m].sum() / p[m].sum(), 2)
    rows.append(row)
print(pd.DataFrame(rows).to_string(index=False))

# figure: observed vs predicted by age band
plt.figure(figsize=(7, 4.5))
xs = np.arange(len(sorted(bands.unique())))
obs, lo_, hi_, labels = [], [], [], []
for b in sorted(bands.unique()):
    m = (bands == b).to_numpy()
    k, m_n = int(y[m].sum()), int(m.sum())
    l, h = wilson(k, m_n)
    obs.append(100 * k / m_n); lo_.append(100 * l); hi_.append(100 * h); labels.append(b)
obs, lo_, hi_ = map(np.array, (obs, lo_, hi_))
plt.errorbar(xs, obs, yerr=[obs - lo_, hi_ - obs], fmt="o", color="black", capsize=3, label="observed")
for name, style in [("3 simple", "s--"), ("3a curved age", "^-")]:
    pm = [100 * oof[name][(bands == b).to_numpy()].mean() for b in sorted(bands.unique())]
    plt.plot(xs, pm, style, label=f"predicted: {name}")
plt.xticks(xs, labels, rotation=20)
plt.ylabel("rate (%)")
plt.title("Undiagnosed diabetes by age band")
plt.legend()
plt.tight_layout()
plt.savefig("figures/age_calibration.png", dpi=120)
plt.close()

# ---------------------------------------------------------------- 3. calibration by race
print("\n=== 3. Observed / expected cases by race/ethnicity (1.0 is ideal) ===")
RACE_NAMES = {1: "Mexican American", 2: "Other Hispanic", 3: "NH White",
              4: "NH Black", 6: "NH Asian", 7: "Other/multi"}
rows = []
for code, label in RACE_NAMES.items():
    m = (df["RIDRETH3"] == code).to_numpy()
    row = {"group": label, "n": int(m.sum()), "cases": int(y[m].sum())}
    for name, p in oof.items():
        row[name] = round(y[m].sum() / p[m].sum(), 2)
    rows.append(row)
print(pd.DataFrame(rows).to_string(index=False))
print("\nQuestion: does the model with race bring these ratios close to 1, and do the")
print("race-free variants change them much? Counts are small, so be cautious.")

print("\nsaved data/oof_week5.csv and figures/age_calibration.png")
