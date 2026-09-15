---
id: dim2
title: Data Foundation & Quality
dimension_number: 2
question_count: 12
---

This dimension assesses whether the data assets supporting AI scenarios have reached the baseline requirements of being "AI-Ready" in terms of **availability, timeliness, accuracy, stability, and performance**.

## 2.1 Data Timeliness

### Q1
**Q1. For the data assets supporting key AI scenarios, are timeliness metrics such as update frequency and data latency explicitly defined and recorded in a queryable SLO/SLA?**

- A. Not defined—the data update cadence relies on "everyone just knows," with no digitized SLO/SLA; timeliness shortfalls are only discovered after a problem occurs
- B. Verbal consensus—the team has an implicit understanding of key-data update frequency (e.g. "roughly T+1"), but it is not formalized into a document or a systematic commitment
- C. Partially documented—core data assets have written timeliness requirements (e.g. an SLA document) covering the main key scenarios, but there is no automated monitoring to verify actual attainment
- D. Systematic SLO/SLA—the data-timeliness metrics of all key AI scenarios are documented and entered into a monitoring system, with a real-time attainment dashboard and alerting; attainment rates are queryable
- N/A. Not applicable—the enterprise currently has no AI scenarios with explicit timeliness requirements

### Q2
**Q2. Do the AI-facing data pipelines (feature generation, embedding computation, index building, etc.) have performance baseline metrics, and has capacity planning or load testing been done?**

- A. No baseline—the data pipelines are "fine as long as they run," with no performance metrics and no capacity planning or load testing done
- B. Basic monitoring—there is basic operational monitoring of the pipelines (e.g. whether they complete successfully), but no explicit performance baseline (throughput, latency, etc.) and no load testing
- C. Baseline and load-tested—key pipelines have defined performance baselines (e.g. p95 latency, QPS ceiling) and have been load-tested at least once to verify capacity
- D. Continuous capacity management—there is a complete performance-baseline system, load testing and capacity planning are conducted on a fixed cadence, capacity is expanded ahead of load growth, and historical trend data supports forecasting
- N/A. Not applicable—the enterprise currently has no AI data pipelines such as feature generation / embedding computation / index building

### Q3
**Q3. In high-concurrency or large-model batch-invocation scenarios, are the necessary performance-protection mechanisms designed?**

- A. No protection—the data layer has no protective design for traffic spikes, so a load surge may render the service unavailable
- B. Basic protection—there is some infrastructure-level protection (e.g. database connection-pool limits), but it is not designed for AI scenarios and lacks active rate-limiting or degradation strategies
- C. Targeted design—caching, rate-limiting, or degradation strategies are designed for the AI call chain, covering at least one core scenario, but have not been validated against real high-concurrency traffic
- D. Complete and validated—there is a systematic performance-protection scheme (caching, tiered storage, rate-limiting, degradation, circuit-breaking) covering the main AI scenarios, validated by load testing or real traffic with a validation record kept
- N/A. Not applicable—the enterprise currently has no high-concurrency or large-model batch-invocation scenarios

## 2.2 Quality Standards and Automated Control

### Q4
**Q4. Are clear quality standards defined for key data assets, and are they checked in the data pipeline via automated rules?**

- A. Not defined—there are no explicit data-quality standards; quality problems are mainly exposed when downstream users "notice something is wrong"
- B. Standards but manual—some quality standards are defined (e.g. completeness, uniqueness), but they are verified mainly by manual spot-checks, with limited coverage and frequency
- C. Partially automated—core data assets have automated quality-check rules embedded in the pipeline (e.g. Great Expectations, dbt tests), ideally covering more than half of the key assets
- D. Fully automated—all key data assets have automated quality rules embedded in the pipeline running continuously; anomalies automatically alert and block downstream consumption
- N/A. Not applicable—the enterprise currently has no explicitly defined list of "key data assets"

### Q5
**Q5. Are AI-adapted quality standards and validation methods defined separately for structured and unstructured data?**

- A. No distinction—there are no quality standards tailored to different data types, or only traditional rules for structured data
- B. Structured only—structured data has fairly complete quality standards, but unstructured data (documents, images, audio, etc.) lacks explicit quality definitions and validation means
- C. Both defined but uneven depth—both data types have defined quality standards (e.g. text noise rate, image resolution), but validation of unstructured data is less automated
- D. Well-classified and automated—both structured and unstructured data have quality standards tailored to AI-consumption needs, each with automated validation tools (e.g. text-cleaning checks, image-quality assessment) and detection records kept
- N/A. Not applicable—the enterprise's AI scenarios involve no unstructured data, or no structured data, so no separate definition is needed

### Q6
**Q6. For AI-facing derived data (chunked text, embedding vectors, search indexes, feature tables, etc.), is there version management and a rollback mechanism?**

- A. No version management—derived data is updated by overwrite, with no historical versions to trace back to
- B. Backup but not versioned—data is backed up occasionally, but there is no systematic version management; rollback requires manual operation and takes a long time
- C. Version management in place—key derived data is version-tagged and archived and can be rolled back when problems occur, but the rollback process is not fully automated and no rollback drill has been done
- D. Versioned and fast-rollback—derived data is comprehensively version-managed with an automated rollback mechanism, at least one rollback drill has been done, and a stable version can be restored in minutes
- N/A. Not applicable—the enterprise currently has no derived data assets such as chunked text, embedding vectors, or indexes

### Q7
**Q7. Are data-quality problems surfaced proactively via an alerting mechanism, with an explicit handling process?**

- A. Passive discovery—when data goes wrong, it is usually business colleagues or model effectiveness that first "feels off" and then comes back to the data team to investigate; the team has no means of finding it in advance itself
- B. Basic alerting—some metrics have alerts (e.g. null-rate over threshold), but alert coverage is incomplete and there is no explicit follow-up handling process
- C. Alerting + handling process—most key data has alert monitoring (not only nulls, but also data-distribution anomalies, sudden metric jumps, etc.), and after a problem there is a set of steps of "locate the problem first, then restore the data, then verify it is fixed"; in most cases someone follows up on handling, but each handling process is not uniformly recorded
- D. Full closed-loop management—all key data is covered by alerts, the handling process is standardized, "how long until it must be responded to and resolved" is specified, and every alert from discovery to closure has a queryable record
- N/A. Not applicable—the enterprise does not yet do quantitative monitoring of data quality (e.g. no automated alert rules have been set)

## 2.3 Data Interpretability and Consistency

### Q8
**Q8. Do the data assets consumed by AI scenarios have machine-readable semantic descriptions (field meaning, business definition, unit, value range, etc.)?**

- A. No semantic description—field meanings are passed on verbally by developers or from personal experience, with no documentation or metadata description
- B. Documented but not machine-readable—there are scattered documents (e.g. Wiki, Confluence pages) explaining field meanings, but they are not in the data catalog and not programmatically accessible
- C. Partially machine-readable—core data assets have metadata descriptions (field meaning, type, value range, etc.) in the data catalog, ideally covering more than half, but updates are not always timely
- D. Comprehensive and automatically maintained—all AI-consumed data assets have complete machine-readable semantic descriptions accessible via the catalog or an API, and kept in sync with source-system changes
- N/A. Not applicable—the enterprise currently has no data catalog or metadata-management tool

### Q9
**Q9. Can the lineage of data assets be traced, in a tool or document, to at least the table/view level?**

- A. Not traceable—the processing chain from source to AI-consumption end cannot be traced; when problems occur, one can only guess from experience
- B. Source traceable—it can be proven that the data is "sourced under control" (e.g. knowing which production database it comes from), but the intermediate processing steps are opaque
- C. Mostly traceable—lineage tools or documents cover the main data assets and can trace to the table/view level, but intermediate steps such as ad-hoc scripts remain blind spots
- D. End-to-end traceable—full-chain lineage is clear and queryable (source → processing → derivation → AI-consumption end), supporting rapid localization of the problem step when AI output is abnormal, with lineage information queryable via a tool rather than recalled by hand
- N/A. Not applicable—the enterprise currently has no data-lineage tool deployed and no corresponding documentation requirement

### Q10
**Q10. For key AI-facing business metrics (order volume, user count, conversion rate, etc.), have the calculation definitions been unified and documented?**

- A. Each defines its own—different teams or scenarios understand and compute the same metric differently, so AI may give contradictory answers across scenarios
- B. Partially unified—a few core metrics have unified definitions, but most metrics are still interpreted by each team on its own, making consistency hard to guarantee
- C. Unified and documented—the calculation definitions of key metrics are unified and documented, but in execution some scenarios still bypass the unified definitions
- D. Unified and enforced—all key metrics have unified definitions, published and documented, and technical means (e.g. a unified metrics layer / semantic layer) guarantee that all consumers get consistent results
- N/A. Not applicable—the enterprise's AI scenarios currently do not involve definition issues for business metrics such as order volume or conversion rate

## 2.4 Quality Incidents and Continuous Improvement

### Q11
**Q11. In the past year, has there been a documented incident showing that, due to a data-quality or timeliness problem, AI output was clearly wrong or had a business impact?**

- A. Unclear—it is uncertain whether such an incident occurred; there is no recording mechanism, so it may have happened but cannot be verified
- B. Happened but not recorded—the team knows related problems occurred, but there is no formal incident record (time, impact, cause)
- C. Partially recorded—serious incidents are recorded (time of occurrence, scope of impact, preliminary cause), but the records are not systematic enough or coverage is incomplete
- D. Systematically recorded—all AI-problem incidents caused by data quality/timeliness are documented, including a detailed timeline, impact assessment, and root-cause analysis
- N/A. Not applicable—the enterprise had no formally running AI scenarios in the past year, so the conditions for such incidents did not exist

### Q12
**Q12. For the above incidents, are there corresponding improvement measures, and have regression checks been completed to confirm the same class of problem does not recur?**

- A. No improvement—once the problem was resolved at the time, it was closed with no systematic improvement measures
- B. Improvement but not verified—improvement measures were made for the incident (e.g. adding rules, adjusting the pipeline), but no regression check was done, so it is uncertain whether they are truly effective
- C. Improved and verified—there are explicit improvement measures and regression checks have been completed to confirm the same class of problem does not recur, but not all historical incidents are covered yet
- D. Closed-loop improvement—every incident has improvement measures, regression checks, and closure confirmation, and the lessons are distilled into new rules or monitoring items, forming a continuous-improvement flywheel
- N/A. Not applicable—no data-quality incident as described in Q11 occurred in the past year
