# Variable dictionary: NHANES 2017-2018

Source: CDC NHANES 2017-2018 public-use files. Join key for all files: SEQN.
"Confirmed" = I read the variable in the CDC Doc File and the entry below matches it.

| Variable | File | Meaning | Codes / units | How load.py handles it | Confirmed |
|---|---|---|---|---|---|
| SEQN | all | Respondent ID | unique per person | merge key (left joins from DEMO_J) | yes |
| RIAGENDR | DEMO_J | Sex | 1 = Male, 2 = Female | kept as is | yes |
| RIDAGEYR | DEMO_J | Age at screening (years) | 0 to 79 = age in years, 80 = 80 years and over, . = missing | adults only: age >= 20 (80 is top-coded) | yes |
| RIDRETH3 | DEMO_J | Race/ethnicity | 1 = Mexican American, 2 = Other Hispanic, 3 = Non-Hispanic White, 4 = Non-Hispanic Black, 6 = Non-Hispanic Asian, 7 = Other race including multi-racial, . = missing | kept as is | yes |
| WTMEC2YR | DEMO_J | Exam sample weight (2-year) | 2566.18 to 419762.84 = range of values, 0 = not MEC examined, . = missing | kept, not used yet | yes |
| BMXBMI | BMX_J | Body mass index | kg/m^2; 12.3 to 86.2 = range of values, . = missing | kept as is | yes |
| BMXWAIST | BMX_J | Waist circumference | cm; 1 = could not obtain, . = missing | kept as is; checked: no values of 1; range 57.9 to 169.5 cm | yes |
| BPXSY1 | BPX_J | Systolic blood pressure, 1st reading | mm Hg; 72 to 228 = range of values, . = missing | kept as is | yes |
| BPXDI1 | BPX_J | Diastolic blood pressure, 1st reading | mm Hg; 0 to 136 = range of values, . = missing | kept as is except readings stored as ~0 (SAS zero artifact, 24 in the final sample) are set to missing | yes |
| LBXGH | GHB_J | Glycohemoglobin (HbA1c) | percent; 3.8 to 16.2 in this cycle, . = missing | defines the outcome; NEVER a model feature | yes |
| DIQ010 | DIQ_J | Doctor ever told you have diabetes | 1 = Yes, 2 = No, 3 = Borderline, 7 = Refused, 9 = Don't know, . = missing | 7 and 9 set to missing; analysis keeps only 2 (never diagnosed); 1 and 3 are excluded | yes |
| MCQ300C | MCQ_J | Close relative had diabetes | 1 = Yes, 2 = No, 7 = Refused, 9 = Don't know, . = missing | 7 and 9 set to missing | yes |
| PAQ635 | PAQ_J | Walk or bicycle for transportation: gate question for PAD645 | 1 = Yes, 2 = No, 7 = Refused, 9 = Don't know, . = missing | 7 and 9 set to missing | yes |
| PAD645 | PAQ_J | Minutes walking/bicycling for transportation | minutes per week; 10 to 660 = range of values, 7777 = refused, 9999 = don't know, . = missing | 7777 and 9999 set to missing; set to 0 if PAQ635 = 2; missing if PAQ635 is missing | yes |
| PAQ650 | PAQ_J | Vigorous recreational activity: gate question for PAD660 | 1 = Yes, 2 = No, 7 = Refused, 9 = Don't know, . = missing | 7 and 9 set to missing | yes |
| PAD660 | PAQ_J | Minutes of vigorous recreational activity | minutes per week; 10 to 480 = range of values, 7777 = refused, 9999 = don't know, . = missing | 7777 and 9999 set to missing; set to 0 if PAQ650 = 2; missing if PAQ650 is missing | yes |

## Derived variable

- undiagnosed = 1 if LBXGH >= 6.5, else 0, among adults with DIQ010 == 2.
- Cutoff source: American Diabetes Association, Standards of Care in Diabetes (diagnostic criteria, Table 2.1); also stated at diabetes.org/about-diabetes/understanding-a1c/diagnosis. Checked 2026-10-24.
- Limitation: guidelines usually require two abnormal tests to confirm a diagnosis. NHANES has one HbA1c per person, so this outcome means "HbA1c at or above 6.5%", not a confirmed clinical diagnosis.

## Not used (and why)

- MCQ092 (blood transfusion) and MCQ151 (age at first menstrual period): not related to the question.