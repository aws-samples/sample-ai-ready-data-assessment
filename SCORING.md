# Scoring & Evaluation Mechanism (Complete Version)

**🌐 Language / 语言:** **English** · [简体中文](./SCORING.zh.md)

Scope: the 45-question version (Dimension 1: 6 questions, Dimension 2: 12 questions, Dimension 3: 12 questions, Dimension 4: 5 questions, Dimension 5: 5 questions, Dimension 6: 5 questions). This document is the **authoritative definition of the scoring rules**, and `scoring/score.py` implements it strictly.

---

## 1. Per-Question Scoring Rules

Each question allows exactly one of the five options A / B / C / D / N/A. The point rules are as follows:

| Option | Points | Meaning |
|---|---|---|
| A | 0 points | Not Started — no relevant mechanism at all, or awareness only |
| B | 1 point | Initial Practice — some local, scattered attempts, not yet systematic |
| C | 2 points | Basic — mechanism established, covers the main scenarios, but automation, validation, and closed-loop still have gaps |
| D | 4 points | Mature/Leading — systematic, automated, continuously validated; a qualitative leap relative to level C |
| N/A | Not scored | The capability/scenario the question asks about does not exist at the enterprise's current stage; it does not count toward the question's score, nor toward the full-marks denominator of its dimension |

**Why the jump from C to D is 2 points rather than an equidistant 1 point:**

The three levels A→B→C describe a gradual progression from "nothing" to "some awareness" to "basically systematic" — this is quantitative change. C→D describes going from "the system has been set up" to "the system actually runs end-to-end, can operate automatically, and can continuously validate its effect"; the threshold crossed here is far higher than any single step among the first three levels — this is a qualitative change, not simply doing a bit more on top. Using an equidistant scale (0/1/2/3) would flatten this qualitative change, causing an enterprise where "most questions are stuck at level C and only a few reach level D" to have a total score that looks close to an enterprise that truly operates systematically, masking the essential gap between the two. Using the 0/1/2/4 scale lets the score more truthfully reflect "whether this enterprise has actually closed the loop, rather than merely appearing to have built a framework."

---

## 2. Dimension Score Calculation

### 2.1 Base Formula

```
Dimension score = Σ sᵢ     (sᵢ is the score of the i-th non-N/A question in that dimension: A=0 / B=1 / C=2 / D=4)
```

### 2.2 Dimension Full Marks and Score Rate

Because the N/A exemption mechanism exists, the "effective full marks" of the same dimension differ across enterprises. Therefore **you cannot divide by a fixed full-marks value directly**; you must use "number of questions actually answered × 4" as the dynamic denominator:

```
Dimension score rate = Dimension score / (number of questions actually answered × 4) × 100%
```

**Theoretical full-marks reference table** (the full marks assuming all questions in the dimension are validly answered with no N/A; for design reference only, not the actual scoring basis):

| Dimension | Questions | Max per question | Theoretical full marks |
|---|---|---|---|
| Dimension 1: Cost & Business Value | 6 | 4 | 24 |
| Dimension 2: Data Foundation & Quality | 12 | 4 | 48 |
| Dimension 3: Platform Architecture & Operations | 12 | 4 | 48 |
| Dimension 4: Organization & Talent | 5 | 4 | 20 |
| Dimension 5: Governance & Trust | 5 | 4 | 20 |
| Dimension 6: Security & Compliance | 5 | 4 | 20 |
| **Total** | **45** | — | **180** |

### 2.3 Two Cases of N/A Handling

- **Some questions in a dimension are N/A**: recalculate the denominator normally as "number of questions actually answered × 4"; this does not affect the scoring of other questions.
- **All questions in a dimension are N/A** (e.g., an enterprise has no Agent scenarios at all, so many questions in Dimension 6 are all inapplicable): this dimension does not participate in the score-rate calculation or the radar-chart comparison. The report should clearly note "this dimension does not currently apply to the assessed subject; the enterprise is advised to re-assess once it reaches the corresponding stage" — rather than showing 0%. Showing 0% would be misread as "security and compliance are done very poorly," when the real situation is "the capability this dimension examines simply does not exist yet"; the two are entirely different in nature.

---

## 3. Total Score Calculation

### 3.1 Total Score Formula (equal-weight version, default)

```
Total score       = Σ Dimension score_d                (d = 1..6)
Overall score rate = Total score / Σ (n_d × 4) × 100%    (n_d = number of questions actually answered in dimension d)
```

By default the six dimensions are naturally weighted by their number of questions (dimensions with more questions naturally take up a larger share of the total), so no extra dimension weight coefficients need to be set.

### 3.2 Optional: Industry/Stage Weight Adjustment (advanced feature)

If the enterprise's industry has higher requirements for certain dimensions (e.g., finance and healthcare should have higher requirements for "Security & Compliance" and "Governance & Trust" than the internet industry), a dimension weight coefficient `w_d` can be introduced:

```
Weighted overall score rate = Σ (w_d × Dimension score rate_d) / Σ w_d
```

By default all `w_d = 1` (equal weight), which reverts to the base formula in 3.1. Whether to enable weighting is recommended as an option at report-generation time (the script's `--weights` parameter) rather than default behavior, to avoid the assessment standard losing comparability due to different weight settings.

---

## 4. Maturity Level Tiers

Tier division is uniformly based on **score rate** (not the raw score); whether for the overall tier or a single dimension's tier, the same set of interval standards applies (intervals are left-closed, right-open `[lo, hi)`, with the top tier L4 including 100%; a boundary value such as exactly 25.0% is placed into the higher tier L2):

| Tier | Score rate interval | Meaning |
|---|---|---|
| L1 Not Started | `[0%, 25%)` | AI-related data capability is essentially blank; most answered questions fall in A/B, lacking basic mechanisms |
| L2 Initial Practice | `[25%, 50%)` | Some scattered practices and local tools exist, but not systematic; relies more on individual experience than on institutions |
| L3 Basic | `[50%, 75%)` | Core mechanisms are established and cover the main scenarios, but automation, validation, and closed-loop still have gaps — typically corresponds to "most questions choose C, a few choose D" |
| L4 Mature & Leading | `[75%, 100%]` | Systematic, automated, traceable, with a continuous-improvement closed loop — only when the proportion of level D is relatively high can this interval be entered |

Because the point gap of C→D is widened to 2 points (twice each step of A→B and B→C), **the actual threshold between L3 and L4 is steeper**: for an enterprise to move from "Basic" to "Mature/Leading," most questions must truly reach level D, and it cannot slip through by having a scattered few D's "pull up the average."

It is recommended to generate two layers of tier labels simultaneously:

1. **Overall tier**: based on the overall score rate, giving the enterprise's overall positioning of AI-Ready data capability.
2. **Per-dimension independent tier**: judged separately based on each dimension's own score rate, helping management see at a glance "which dimension is the weak spot and which is already leading," rather than having structural imbalance masked by the total score.

---

## 5. Scoring Example (with old-vs-new scale comparison)

Suppose an enterprise answers Dimension 2 (Data Foundation & Quality, 12 questions) as follows: 2 questions choose A, 2 choose B, 6 choose C, 2 choose D, 0 N/A.

```
Dimension 2 score      = 2×0 + 2×1 + 6×2 + 2×4 = 0 + 2 + 12 + 8 = 22 points
Dimension 2 score rate = 22 / (12×4) = 22/48 ≈ 45.8%
```

Against the tier table, 45.8% falls in the high end of the **L2 Initial Practice** interval, close to but not reaching L3.

**Comparison with the old scale** (A=0 / B=1 / C=2 / D=3) for the same set of answers:

```
Old-scale score = 2×0 + 2×1 + 6×2 + 2×3 = 20 points, full marks 36, score rate ≈ 55.6%
```

Under the old scale, 55.6% would be classified as **L3 Basic**, but under the new scale it is only 45.8%, still remaining in L2. This difference precisely reflects the intent of the new scale: in this set of answers, level D accounts for only 2/12 (about 17%), and most questions still remain at level C — "basically meeting standards but without a closed loop." The new scale more accurately classifies it as "the high end of Initial Practice" rather than jumping straight up to "Basic."

---

## 6. Report Presentation Guidance

- **Radar chart**: the six axes each represent the score rate (0%–100%) of one of the six dimensions, not the raw score, ensuring cross-dimension comparability.
- **Overall tier label**: next to the radar chart, annotate the L1–L4 label corresponding to the overall score rate.
- **Per-dimension tier labels**: on each axis, also annotate that dimension's individual L1–L4 label, used to quickly locate weak spots.
- **Special annotation for N/A dimensions**: if a dimension is excluded from the radar-chart comparison because it is entirely N/A, the reason must be noted in a prominent place in the report to avoid being misread as a "zero score."
- **Display the level-D proportion separately** (optional advanced): in addition to the total score and score rate, also display "the proportion of level-D questions among the questions actually answered." This metric more intuitively shows how much of an enterprise's capability truly reaches the level of "systematic + automated + verifiable closed loop," rather than being "averaged" by the number of level-C answers into a score that looks decent.
- **Always carry the questionnaire version**: a result is only comparable against another result produced by the **same questionnaire version**, so the version must travel with the numbers. `score.py` stamps it automatically — as `questionnaire: v<x.y.z>` in the human-readable report and as the `questionnaire_version` key in `--json` output, read from [`VERSION`](./VERSION). A year-on-year or cross-business-unit comparison that spans two questionnaire versions must say so explicitly; see the versioning rules in [`CONTRIBUTING.md`](./CONTRIBUTING.md#questionnaire-versioning-ensuring-cross-version-comparability).
