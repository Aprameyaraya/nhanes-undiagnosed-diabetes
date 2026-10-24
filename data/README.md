# Data log: NHANES 2017-2018 undiagnosed diabetes

Last updated: 2026-10-24

## Goal
Estimate how well easily measured factors (age, sex, race/ethnicity, BMI, waist, blood
pressure, physical activity, family history) identify adults who have diabetes but have
not been diagnosed, and check whether performance is similar across groups.

## Data source
CDC NHANES 2017-2018 cycle, public-use files, downloaded on [date you downloaded]
from the CDC NHANES site (Demographics, Examination, Laboratory and Questionnaire pages).

Files used (saved in data/raw/, not committed to git):
DEMO_J, BMX_J, BPX_J, GHB_J, DIQ_J, PAQ_J, MCQ_J

## How the dataset was built
Run `python src\load.py` from the project root. It merges all files on SEQN (left joins
from DEMO_J), cleans the data, and writes data/merged.csv.

## Sample selection
| Step | Count |
|---|---|
| All respondents (DEMO_J) | 9,254 |
| Adults, age 20 or older | 5,569 |
| Dropped: missing HbA1c or DIQ010 | 555 |
| Excluded: previously diagnosed (DIQ010 = 1) | 804 |
| Excluded: borderline (DIQ010 = 3) | 159 |
| **Final analysis sample** | **4,051** |

## Outcome
Undiagnosed diabetes = HbA1c >= 6.5% among adults who report no diabetes diagnosis
(DIQ010 = 2). [Cutoff source: American Diabetes Association, Standards of Care in Diabetes (diagnostic criteria, Table 2.1); also stated on diabetes.org/about-diabetes/understanding-a1c/diagnosis. Checked 2026-10-24.]
Result: 150 cases (3.7%), 3,901 non-cases.

Diagnosed adults are excluded on purpose: this is a screening question about people who
do not know they have diabetes, and labeling diagnosed people "negative" would be wrong.
Borderline answers are excluded because their status is ambiguous.

## Missing data (fraction of the final sample)
BPXSY1 and BPXDI1: 11.0% | BMXWAIST: 4.8% | BMXBMI: 1.4% | MCQ300C: 1.1%
PAD645: 0.2% | PAD660: 0.1% | all other variables: 0%
Handling plan: impute inside cross-validation folds only, to avoid leakage. [Update later.]

## Known limitations
- Only 150 positive cases, so estimates for subgroups will be uncertain.
- The 555 adults dropped for missing HbA1c or DIQ010 may differ from those kept
  (not yet checked).
- One survey cycle only; survey weights are not yet used.
- HbA1c is a single measurement and may not match a clinical diagnosis exactly.
- LBXGH defines the outcome and must never be used as a model feature.
- Guidelines usually require two abnormal tests to confirm a diagnosis, but NHANES gives only one HbA1c per person, therefore it is not a confirmed clinical diagnosis.

## Next steps
Week 2: exploration (prevalence by group, distributions, missing-data checks).

BPXDI1 readings of 0 (24 in the final sample) treated as missing; assumed to be a measurement artifact