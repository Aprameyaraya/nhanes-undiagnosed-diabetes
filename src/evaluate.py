"""
Week 4: calibration, subgroup performance, thresholds and paired comparisons.

Run from the project root (with your .venv active):
    python src/evaluate.py

Uses data/oof_predictions.csv from model.py. Every prediction there came from a model
that did NOT see that person (10-fold out-of-fold), so these are fair estimates, though
still from one cycle of data. Race is used here ONLY to group people for checking
performance, never as a model input (models 3 and 4).

Column names in oof_predictions.csv:
  3_logistic = simple model (age, BMI, family history, systolic BP)
  4_logistic = all features, no race
  5_logistic = all features + race (comparison only)
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

RNG = np.random.default_rng(42)
N_BOOT = 1000
MIN_PER_CLASS = 15          # do not report subgroup AUROC with fewer cases than this

oof = pd.read_csv("data/oof_predictions.csv")
y = oof["undiagnosed"].to_numpy()
os.makedirs("figures", exist_ok=True)

PRIMARY = "3_logistic"
OTHERS = {"3_logistic": "3 simple (no race)",
          "4_logistic": "4 all features (no race)",
          "5_logistic": "5 with race (comparison only)"}
RACE = {1: "Mexican American", 2: "Other Hispanic", 3: "NH White",
        4: "NH Black", 6: "NH Asian", 7: "Other/multi"}
SEX = {1: "Male", 2: "Female"}


def wilson(k, n, z=1.96):
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return centre - half, centre + half


def auc_ci(y_, p_):
    """AUROC with a bootstrap 95% interval (resampling people)."""
    base = roc_auc_score(y_, p_)
    n, vals = len(y_), []
    for _ in range(N_BOOT):
        idx = RNG.integers(0, n, n)
        yb = y_[idx]
        if yb.min() == yb.max():
            continue
        vals.append(roc_auc_score(yb, p_[idx]))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return base, lo, hi


def paired_diff(y_, pa, pb):
    """Bootstrap interval for AUROC(a) - AUROC(b) using the same resamples."""
    n, diffs = len(y_), []
    for _ in range(N_BOOT):
        idx = RNG.integers(0, n, n)
        yb = y_[idx]
        if yb.min() == yb.max():
            continue
        diffs.append(roc_auc_score(yb, pa[idx]) - roc_auc_score(yb, pb[idx]))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return np.mean(diffs), lo, hi


# ------------------------------------------------------------------------------
# 1. Overall discrimination with intervals, and paired comparisons
# ------------------------------------------------------------------------------
print("=== 1. Overall AUROC (bootstrap 95% CI) ===")
for col, label in OTHERS.items():
    a, lo, hi = auc_ci(y, oof[col].to_numpy())
    print(f"{label:32s} {a:.3f}  ({lo:.3f} to {hi:.3f})")

print("\nPaired differences in AUROC (positive = first model better):")
pairs = [("3_logistic", "4_logistic"), ("5_logistic", "3_logistic"), ("5_logistic", "4_logistic")]
for a, b in pairs:
    d, lo, hi = paired_diff(y, oof[a].to_numpy(), oof[b].to_numpy())
    print(f"{OTHERS[a]} minus {OTHERS[b]}: {d:+.3f}  ({lo:+.3f} to {hi:+.3f})")
print("If the interval includes 0, the difference is unclear.")

# ------------------------------------------------------------------------------
# 2. Calibration
# ------------------------------------------------------------------------------
print("\n=== 2. Calibration (5 groups by predicted risk) ===")
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
for ax, col in zip(axes, ["3_logistic", "4_logistic"]):
    p = oof[col].to_numpy()
    tab = pd.DataFrame({"bin": pd.qcut(p, 5, labels=False, duplicates="drop"), "p": p, "y": y})
    g = tab.groupby("bin").agg(n=("y", "size"), cases=("y", "sum"), pred=("p", "mean"))
    g["obs"] = g["cases"] / g["n"]
    ci = np.array([wilson(k, n) for k, n in zip(g["cases"], g["n"])])
    g["obs_lo"], g["obs_hi"] = ci[:, 0], ci[:, 1]
    print(f"\n{OTHERS[col]}")
    print((g.assign(pred=lambda d: d.pred * 100, obs=lambda d: d.obs * 100,
                    obs_lo=lambda d: d.obs_lo * 100, obs_hi=lambda d: d.obs_hi * 100)
           .round(2)).to_string())

    logit = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(logit.reshape(-1, 1), y)
    print(f"mean predicted {p.mean() * 100:.2f}% vs observed {y.mean() * 100:.2f}%; "
          f"calibration slope {lr.coef_[0, 0]:.2f} (1.0 is ideal)")

    ax.errorbar(g["pred"] * 100, g["obs"] * 100,
                yerr=[(g["obs"] - g["obs_lo"]) * 100, (g["obs_hi"] - g["obs"]) * 100],
                fmt="o", capsize=3)
    top = max(g["pred"].max(), g["obs_hi"].max()) * 100 * 1.1
    ax.plot([0, top], [0, top], "--", color="gray")
    ax.set_xlabel("mean predicted risk (%)")
    ax.set_ylabel("observed rate (%)")
    ax.set_title(OTHERS[col])
plt.tight_layout()
plt.savefig("figures/calibration.png", dpi=120)
plt.close()

# ------------------------------------------------------------------------------
# 3. Performance within groups (primary model)
# ------------------------------------------------------------------------------
print(f"\n=== 3. Performance within groups: {OTHERS[PRIMARY]} ===")
print("O/E = observed cases / expected cases (sum of predicted risks). 1.0 is ideal;")
print("above 1 means the model under-predicts that group, below 1 means over-predicts.")
print(f"AUROC shown only if each class has at least {MIN_PER_CLASS} people.\n")
p_main = oof[PRIMARY].to_numpy()
oof["age_band"] = pd.cut(oof["RIDAGEYR"], [20, 30, 40, 50, 60, 70, 81], right=False).astype(str)
oof["sex"] = oof["RIAGENDR"].map(SEX)
oof["race"] = oof["RIDRETH3"].map(RACE)

for col, title in [("sex", "sex"), ("age_band", "age band"), ("race", "race/ethnicity")]:
    rows = []
    for level, idx in oof.groupby(col).groups.items():
        m = oof.index.isin(idx)
        yy, pp = y[m], p_main[m]
        cases, n = int(yy.sum()), int(m.sum())
        row = {title: level, "n": n, "cases": cases,
               "mean_pred_%": round(pp.mean() * 100, 2), "observed_%": round(yy.mean() * 100, 2),
               "O/E": round(cases / pp.sum(), 2)}
        if cases >= MIN_PER_CLASS and (n - cases) >= MIN_PER_CLASS:
            a, lo, hi = auc_ci(yy, pp)
            row["AUROC (95% CI)"] = f"{a:.2f} ({lo:.2f} to {hi:.2f})"
        else:
            row["AUROC (95% CI)"] = "too few cases"
        rows.append(row)
    print(f"--- by {title} ---")
    print(pd.DataFrame(rows).to_string(index=False))
    print()

# ------------------------------------------------------------------------------
# 4. Thresholds: what happens if we flag the highest-risk people?
# ------------------------------------------------------------------------------
print(f"=== 4. Flagging the highest-risk people ({OTHERS[PRIMARY]}) ===")
rows = []
for frac in [0.10, 0.20, 0.30]:
    cut = np.quantile(p_main, 1 - frac)
    flag = p_main >= cut
    tp = int((flag & (y == 1)).sum())
    fp = int((flag & (y == 0)).sum())
    fn = int((~flag & (y == 1)).sum())
    tn = int((~flag & (y == 0)).sum())
    ppv = tp / (tp + fp)
    rows.append({"flag top": f"{int(frac * 100)}%", "risk cutoff_%": round(cut * 100, 2),
                 "sensitivity_%": round(100 * tp / (tp + fn), 1),
                 "specificity_%": round(100 * tn / (tn + fp), 1),
                 "PPV_%": round(100 * ppv, 1), "NPV_%": round(100 * tn / (tn + fn), 1),
                 "people flagged": tp + fp, "flagged per case found": round(1 / ppv, 1)})
print(pd.DataFrame(rows).to_string(index=False))

print("\nSensitivity by group when the top 20% overall are flagged (one shared cutoff):")
cut20 = np.quantile(p_main, 0.80)
flag20 = p_main >= cut20
rows = []
for level, idx in oof.groupby("race").groups.items():
    m = oof.index.isin(idx)
    cases = int(y[m].sum())
    caught = int((flag20 & m & (y == 1)).sum())
    lo, hi = wilson(caught, cases) if cases else (np.nan, np.nan)
    rows.append({"race/ethnicity": level, "cases": cases, "caught": caught,
                 "sensitivity_%": round(100 * caught / cases, 1) if cases else np.nan,
                 "CI_low_%": round(100 * lo, 1), "CI_high_%": round(100 * hi, 1),
                 "share flagged_%": round(100 * flag20[m].mean(), 1)})
print(pd.DataFrame(rows).to_string(index=False))
print("\nWide intervals mean small samples: do not read differences between groups as real")
print("unless the intervals are clearly apart.")

print("\nsaved figures/calibration.png")
