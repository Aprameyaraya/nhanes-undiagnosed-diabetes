# Week 3: Baseline and candidate models

Data: NHANES 2017-2018, adults 20+ with no prior diabetes diagnosis (n = 4,051, 150 cases, 3.7%).
Method: 5-fold cross-validation repeated 5 times (25 folds per model). Imputation and scaling
are fit inside each training fold. Hyperparameters are fixed (no tuning). The "no information"
reference is a model that predicts the overall prevalence for everyone.

## Results (mean over 25 folds)

| Model | AUROC | AUROC SD | Avg precision | Brier | Log loss |
|---|---|---|---|---|---|
| 0 Prevalence only (reference) | 0.500 | 0.000 | 0.037 | 0.0357 | 0.1584 |
| 1 Age only | 0.645 | 0.034 | 0.054 | 0.0354 | 0.1542 |
| 2 Age + BMI | 0.724 | 0.036 | 0.098 | 0.0351 | 0.1479 |
| 3 Simple: age, BMI, family history, systolic BP | 0.747 | 0.038 | 0.099 | 0.0351 | 0.1461 |
| 4 All features, no race (logistic) | 0.737 | 0.039 | 0.094 | 0.0352 | 0.1471 |
| 5 All features + race (logistic) | 0.785 | 0.029 | 0.128 | 0.0345 | 0.1400 |
| 6 All features + race (gradient boosting) | 0.776 | 0.030 | 0.143 | 0.0344 | 0.1414 |

AUROC SD is the spread across folds, not a confidence interval. I treat differences smaller
than about 0.02 AUROC as unclear.

## 1. Which model is best?

Models 5 and 6 are the best. Model 5 (logistic, all features plus race) has the highest AUROC
(0.785) and the lowest log loss (0.1400). Model 6 (gradient boosting) has the highest average
precision (0.143) and the lowest Brier score (0.0344), but its AUROC is slightly lower (0.776).
The differences between 5 and 6 are small compared with the fold-to-fold spread, so I cannot
say one is better. Because logistic regression is simpler and easier to explain, I would
prefer it unless a later test shows boosting is clearly better.

## 2. What helped and what did not

- **Age alone** is better than chance (AUROC 0.645) but weak.
- **Adding BMI** is the biggest early gain (0.645 to 0.724).
- **Adding family history and systolic BP** gives a smaller gain (0.724 to 0.747), roughly
  one fold-SD, so it is suggestive but not certain.
- **Adding everything else without race** (waist, diastolic BP, sex, activity, missing-value
  indicators) did not help: 0.737 vs 0.747 for the simple model. The extra variables carry
  little new information or add noise.
- **Adding race** gives the largest single jump after BMI: 0.737 to 0.785.
- **Gradient boosting** did not clearly beat logistic regression.

## 3. Simple vs full model

The simple model (age, BMI, family history, systolic BP) loses nothing against the full model
without race (0.747 vs 0.737) and uses four easy-to-collect measurements. The full model with
race is better by about 0.04 AUROC. A simple model is attractive for a screening tool.
Whether to use race as an input is a design and fairness question, not just a performance one
(see section 6).

## 4. Coefficients of the full logistic model (model 5, for interpretation only)

Numeric variables are standardized, so their coefficients are log-odds per 1 SD. Binary and
race indicators are not standardized (they are log-odds for the category), so I should not
compare their sizes directly with the numeric ones.

- Largest: race indicators. Non-Hispanic White is strongly negative (-1.38), consistent with
  the week 2 finding that this group has a much lower rate (1.3%). Non-Hispanic Asian is
  positive (+0.78) after adjusting for the other variables. Non-Hispanic Black is near zero
  (-0.01) even though its raw rate was about 5%, which means its higher raw rate is mostly
  explained by the other variables in the model. These race coefficients are not relative to
  a reference group (the penalty spreads weight across all categories), so they should be
  read as differences from an average.
- Age (+0.56), family history (+0.51) and waist (+0.46) are the next largest, in the
  directions seen in week 2.
- Systolic BP (+0.22) and BMI (+0.21) are smaller. Waist has a larger coefficient than BMI,
  probably because the two are highly correlated and the model splits the weight.
- Sex (+0.17), diastolic BP (-0.05), walking (-0.11) and vigorous activity (-0.15) are small.
- Missing-value indicators are all small (|coef| below 0.22).

## 5. How good is it, really?

- AUROC of about 0.75 to 0.79 is moderate discrimination, not strong.
- Average precision of 0.13 to 0.14 is about 3.5 times the baseline (0.037), but it also means
  most people flagged as high risk would not actually have undiagnosed diabetes.
- Brier score improves only from 0.0357 to 0.0345 (about 3%), which is expected for a rare
  outcome, so it is not informative on its own. Log loss improves by about 12%.
- These estimates come from cross-validation on the same data used to choose the models, so
  they are probably somewhat optimistic. I still need an external check on a different cycle.

## 6. Open questions

- Should race be an input? It improves the numbers, but a screening model that uses race can
  produce different risk for groups for reasons that data alone cannot explain, and race here
  may stand in for things I did not measure. I need to look at how the models perform within
  each group before deciding.
- Is the waist-versus-BMI difference real? Test a model with waist in place of BMI.
- Are the predicted probabilities calibrated? I have not checked yet.

## Next (week 4)

Calibration plots and metrics from out-of-fold predictions; performance by sex, age band and
race/ethnicity with confidence intervals (bootstrap); a look at thresholds (sensitivity,
specificity and positive predictive value); a paired comparison of models 3 and 5.