# Week 4: Evaluation, calibration, subgroups and thresholds

Data: NHANES 2017-2018, adults 20+ with no prior diabetes diagnosis (n = 4,051, 150 cases, 3.7%).
Predictions: 10-fold out-of-fold, so each person was scored by a model that never saw them.
Intervals: bootstrap 95% intervals (1,000 resamples of people). Everything is unweighted and
comes from one survey cycle.

## Decision: race is not a model input

I decided not to use race/ethnicity as an input. Race is still used to group people so I can
check how the model behaves in each group. The cost of this choice, measured against the
model that includes race:

- AUROC 0.744 (simple model, no race) vs 0.784 (with race).
- Paired difference: +0.040 (95% CI +0.011 to +0.065), so the loss is small but probably real.

The primary model from here on is **model 3** (age, BMI, family history, systolic BP).
Reasons: it is not clearly worse than the all-features model without race (paired difference
+0.010, CI -0.001 to +0.022), it is better calibrated (slope 0.94 vs 0.87), and it needs only
four easy measurements.

## 1. Overall discrimination

| Model | AUROC (95% CI) |
|---|---|
| 3 Simple (no race) | 0.744 (0.710 to 0.778) |
| 4 All features (no race) | 0.734 (0.701 to 0.766) |
| 5 With race (comparison only) | 0.784 (0.752 to 0.812) |

The extra variables in model 4 (waist, diastolic BP, sex, activity) add nothing clear
beyond model 3. Moderate discrimination overall.

## 2. Calibration (model 3)

Average predicted risk matches the observed rate overall (3.70% vs 3.70%), and the
calibration slope is 0.94 (1.0 is ideal), so the predictions are only slightly too spread out.

| Risk group (fifths) | n | Cases | Predicted % | Observed % (95% CI) |
|---|---|---|---|---|
| Lowest | 811 | 0 | 0.81 | 0.00 (0.00 to 0.47) |
| 2nd | 810 | 15 | 1.66 | 1.85 (1.13 to 3.03) |
| 3rd | 810 | 22 | 2.70 | 2.72 (1.80 to 4.08) |
| 4th | 810 | 45 | 4.18 | 5.56 (4.18 to 7.35) |
| Highest | 810 | 68 | 9.16 | 8.40 (6.68 to 10.51) |

The middle groups agree well. The lowest group had no cases at all although about 6 were
expected, so the model slightly over-predicts at the very low end (a small difference in
absolute terms). The fourth group is slightly under-predicted (the interval just reaches the
predicted value). Model 4 has a worse slope (0.87), meaning its predictions are more
over-spread.

## 3. Performance within groups (model 3)

O/E = observed cases divided by expected cases. Above 1 means the model under-predicts the
group, below 1 means it over-predicts. AUROC is shown only with at least 15 people per class.

**Sex.** Women: AUROC 0.78 (0.74 to 0.82), O/E 1.06. Men: AUROC 0.68 (0.62 to 0.74), O/E 0.92.
Calibration is reasonable in both. The model may rank women better, but the intervals only
just touch, so this is suggestive and not conclusive.

**Age.** Within each age band the AUROC is only 0.65 to 0.73, lower than the overall 0.744.
Much of the overall discrimination comes from age itself. Calibration by age is uneven:

| Age | Cases | Predicted % | Observed % | O/E |
|---|---|---|---|---|
| 20-29 | 6 | 1.41 | 0.84 | 0.59 |
| 30-39 | 13 | 2.28 | 1.79 | 0.79 |
| 40-49 | 17 | 3.07 | 2.69 | 0.87 |
| 50-59 | 44 | 4.09 | 6.41 | 1.57 |
| 60-69 | 42 | 5.45 | 6.10 | 1.12 |
| 70+ | 28 | 6.34 | 4.64 | 0.73 |

The model under-predicts people in their 50s (observed 6.4% vs predicted 4.1%) and
over-predicts the oldest and youngest. This fits the week 2 pattern where the rate rises
until about age 50-60 and then levels off or dips, while the model treats age as a straight
line. Idea to test: let age have a curved effect.

**Race/ethnicity (not a model input).**

| Group | n | Cases | Predicted % | Observed % | O/E | AUROC (95% CI) |
|---|---|---|---|---|---|---|
| NH White | 1,424 | 19 | 3.91 | 1.33 | 0.34 | 0.78 (0.72 to 0.84) |
| NH Asian | 562 | 29 | 2.44 | 5.16 | 2.12 | 0.80 (0.73 to 0.87) |
| NH Black | 921 | 48 | 4.52 | 5.21 | 1.15 | 0.73 (0.66 to 0.79) |
| Mexican American | 544 | 25 | 3.35 | 4.60 | 1.37 | 0.74 (0.64 to 0.83) |
| Other Hispanic | 397 | 20 | 3.49 | 5.04 | 1.45 | 0.76 (0.68 to 0.83) |
| Other/multi | 203 | 9 | 3.39 | 4.43 | 1.31 | too few cases |

Ranking ability within each group is similar (the AUROC intervals overlap). But the
absolute risk levels are off by group. For non-Hispanic White adults about 56 cases are
expected and only 19 occur, so the model over-predicts them by a lot. For non-Hispanic Asian
adults about 14 cases are expected and 29 occur, so it under-predicts them by about half.
These gaps are large relative to the counts, so they are unlikely to be only chance, though
I did not run a formal test. Something to look up: whether diabetes risk differs by group
at the same BMI (I have not verified this).

## 4. Thresholds (model 3, flagging the highest-risk people)

| Flag top | Risk cutoff % | Sensitivity % | Specificity % | PPV % | NPV % | People flagged | Flagged per case found |
|---|---|---|---|---|---|---|---|
| 10% | 7.72 | 25.3 | 90.6 | 9.4 | 96.9 | 406 | 10.7 |
| 20% | 5.28 | 45.3 | 81.0 | 8.4 | 97.5 | 811 | 11.9 |
| 30% | 4.13 | 64.7 | 71.3 | 8.0 | 98.1 | 1,216 | 12.5 |

Flagging the top 30% finds about two thirds of cases, but only about 8% of flagged people
actually have undiagnosed diabetes. That is about 2.2 to 2.5 times the base rate of 3.7%
(testing a random person finds a case once per 27 people), so the model helps, but modestly.
NPV is about 97 to 98%, only a little above the 96.3% you get by assuming nobody has it.

With one shared cutoff (top 20% overall), sensitivity and flag rates differ by group:

| Group | Cases | Caught | Sensitivity % (95% CI) | Share flagged % |
|---|---|---|---|---|
| NH Black | 48 | 29 | 60.4 (46.3 to 73.0) | 25.6 |
| Other Hispanic | 20 | 9 | 45.0 (25.8 to 65.8) | 19.1 |
| Mexican American | 25 | 11 | 44.0 (26.7 to 62.9) | 15.8 |
| NH White | 19 | 8 | 42.1 (23.1 to 63.7) | 23.5 |
| Other/multi | 9 | 3 | 33.3 (12.1 to 64.6) | 18.2 |
| NH Asian | 29 | 8 | 27.6 (14.7 to 45.7) | 7.5 |

Only the NH Asian vs NH Black gap has non-overlapping intervals (14.7 to 45.7 vs 46.3 to
73.0). The pattern matches the calibration findings: a shared cutoff flags about 24% of NH
White adults, whose true rate is low, and only 7.5% of NH Asian adults, whose true rate is
high, so the model misses more of their cases.

## 5. What this means

- The model is moderately useful for ranking risk but not precise. Most people it flags
  do not have the condition, which is expected for a 3.7% outcome.
- Leaving race out of the inputs does not make the model behave the same way for everyone.
  Predictions are too high for one group and too low for another.
- Possible responses, each with costs: add race back (improves the numbers but is
  ethically contested), add better predictors, or keep the model and report the
  limitation clearly. I should state my choice and the evidence.

## 6. Limitations

- One survey cycle, unweighted analysis, 150 cases in total.
- Group results rest on small counts (for example 19 cases for NH White, 9 for Other/multi).
- Out-of-fold estimates are from the same data used to compare models, so they may be
  somewhat optimistic. An external check on a different NHANES cycle is still needed.
- Only one HbA1c measurement defines the outcome.

## Next

- Test age with a curved effect and see whether the age-band calibration improves.
- Check calibration by group for the model that includes race (model 5), to see whether it
  actually fixes the group gaps.
- Swap BMI for waist in the simple model (still untested).
- External validation on the 2015-2016 cycle.