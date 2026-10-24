# Week 2: Exploratory analysis

Data: NHANES 2017-2018, adults 20+ with no previous diabetes diagnosis (n = 4,051).
Outcome: undiagnosed diabetes = HbA1c >= 6.5% (150 cases, 3.7%).
All figures are unweighted, so they describe this sample and not the US population.
Intervals are 95% Wilson confidence intervals. When two groups' intervals do not overlap,
I treat the difference as likely real; when they overlap, I treat it as unclear.

## 1. Prevalence by group

**Age.** Prevalence rises from 0.8% (CI 0.4 to 1.8) at ages 20-29 to 6.4% (CI 4.8 to 8.5)
at ages 50-59, with a clear step up between the 40s (2.7%, CI 1.7 to 4.3) and the 50s.
It then levels off: 6.1% at 60-69 and 4.6% (CI 3.2 to 6.6) at 70+. Those last three
intervals overlap, so I cannot say the rate really falls after 70. The 50-59 and 60-69
bands hold 86 of the 150 cases (57%) but only about 34% of the sample (1,374 of 4,051),
so the rate there is higher, not just the count.

**Sex.** 3.2% in men (CI 2.5 to 4.1, n = 1,889) and 4.2% in women (CI 3.4 to 5.1, n = 2,162).
The intervals overlap, so there is no clear sex difference. Women have more cases (90 vs 60)
partly because there are more women in the sample (53%).

**Race/ethnicity.** Non-Hispanic White adults have a much lower rate (1.3%, CI 0.9 to 2.1,
n = 1,424) than every other group: Mexican American 4.6%, Other Hispanic 5.0%, non-Hispanic
Black 5.2% (CI 4.0 to 6.8, n = 921), non-Hispanic Asian 5.2%, Other/multiracial 4.4%.
The White interval does not overlap with any of the others. The other groups overlap with
each other, so I cannot rank them. Non-Hispanic Black adults have the most cases (48)
mostly because it is a large group in this sample, but their rate is also about four times
the non-Hispanic White rate. NHANES deliberately oversamples some groups, so group sizes
reflect the survey design.

**BMI.** Prevalence rises steadily with BMI: 1.3% (under 25), 2.5% (25-30), 5.0% (30-35),
7.7% (35 and over). The lowest and highest bands differ by about six times and their
intervals do not overlap (0.8 to 2.2 vs 6.0 to 9.9). The neighbouring bands overlap
somewhat (for example 30-35 vs 35+), but the trend is clear.

**Family history.** Prevalence is 5.0% with a close relative with diabetes (CI 4.1 to 6.1,
n = 1,724) vs 2.7% without (CI 2.1 to 3.5, n = 2,281). The intervals do not overlap, so
family history is clearly associated with the outcome in this sample, about 1.9 times higher.
This has not been adjusted for age or BMI.

## 2. Differences between cases and non-cases (medians)

| Variable | No diabetes | Undiagnosed diabetes |
|---|---|---|
| Age (years) | 48.0 | 58.5 |
| BMI | 28.0 | 32.3 |
| Waist (cm) | 97.4 | 109.0 |
| Systolic BP (mm Hg) | 122 | 132 |
| Diastolic BP (mm Hg) | 72 | 74 |
| Walk/bike minutes per week | 0 | 0 |
| Vigorous recreation minutes per week | 0 | 0 |

Cases are older, heavier, have larger waists and higher systolic pressure. Diastolic
pressure differs little. The activity medians are both 0 because most people report no
such activity, so the median is not informative; I need a different summary, such as the
share of people with any activity. According to the graphs measuring diabetes rates against BMI, Waist size, Blood Pressure and age, there is major overlapping of cases and non-cases for BMI, Waist Size and blood pressure. Only the Age graph shows a clear shift between cases and non-cases, with more cases appearing in the age range of 50 to 70 years.

## 3. Missing blood pressure

Outcome rate is 3.6% when systolic BP is measured (n = 3,606) and 4.7% when missing
(n = 445, about 21 cases). The missing group is small, so its rate is imprecise (roughly
3% to 7%) and the difference is within what chance could produce. Missingness does not
look strongly related to the outcome, but I cannot rule out a small link.

## 4. Adults without a usable label (missing HbA1c or diabetes answer)

555 adults had no label vs 5,014 who did. They look similar on average age (51.0 vs 51.6),
percent female (48.1% vs 51.9%) and BMI (29.4 vs 29.9). The race/ethnicity mix differs a
little: more non-Hispanic Black (26.8% vs 22.9%) and non-Hispanic Asian (18.6% vs 14.1%)
adults, fewer Mexican American and Other Hispanic adults, and about the same share of
non-Hispanic White adults. These are descriptive differences and I have not tested them.
I cannot know their outcome rate, so this is a limitation.

## 5. Surprises and open questions

- Non-Hispanic White adults have a much lower rate than all other groups. This data cannot
  say why. Whether someone is undiagnosed depends on access to testing as well as on
  disease, so I should not read this as only a difference in who gets diabetes.
- The rate does not keep rising after age 60, but the intervals overlap so I cannot say
  it falls.
- Family history shows a clear difference, which I had expected to be weaker.

## 6. What this suggests for modeling (week 3)

- Likely useful: age, BMI or waist, family history, race/ethnicity, systolic BP.
- Weak or unclear: sex, diastolic BP.
- BMI and waist are probably highly correlated, so check that and consider keeping one.
- These patterns are unadjusted. Age, BMI and family history overlap, so a model is needed
  to see what each adds.
- Only 150 cases, so subgroup results are uncertain. Use cross-validation and report
  confidence intervals.