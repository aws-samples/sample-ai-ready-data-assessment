---
id: dim3
title: Platform Architecture & Operations
dimension_number: 3
question_count: 12
---

This dimension assesses whether the enterprise's data platform has evolved from a traditional data-processing foundation into a capability that can stably support the data supply required for large-model invocation, retrieval augmentation, knowledge bases, and multi-agent orchestration. It covers the unified access to data services, observability on the data side, elastic capacity assurance for data, impact control of data changes, and the level of intelligent operations of the data platform itself.

## 3.1 Do Data Services Uniformly Support the AI Stack

### Q1
**Q1. Are AI-facing data services (feature serving, vector retrieval, knowledge-base queries, context recall, etc.) provided through a unified interface, rather than each AI scenario building its own data-access approach?**

- A. Every scenario for itself—each AI scenario develops its own data-access logic, and may even maintain its own copy of the data, so data-service capability is neither accumulated nor reused
- B. Partially unified—a few data services (e.g. a certain feature table or a certain knowledge base) are shared and called by multiple scenarios, but most scenarios still build their own data-access chains
- C. Basically unified—most AI scenarios obtain the data they need (features, vectors, knowledge-base content, etc.) through unified data-service interfaces, so new scenarios do not need to rebuild data pipelines when onboarding
- D. Fully unified and reusable—the data supply for all AI scenarios is fulfilled through a unified data-service layer; new scenarios can directly reuse existing data interfaces and pipelines, and the data service itself continues to evolve as a platform capability
- N/A. Not applicable—the enterprise currently has few AI scenarios in number or type, so there is no need yet to reuse data services

### Q2
**Q2. Is there a unified identity and permission mechanism that governs the scope of data access by AI agents or AI applications (which tables, which fields, which knowledge bases they can read)?**

- A. No unified management—the data-access permissions of AI applications or agents are configured by each scenario on its own, lacking a unified data-access-boundary control
- B. Basic control—there is a basic access-credential mechanism (e.g. a unified data-interface key), but the permission granularity is coarse and cannot finely control access to specific tables, fields, or knowledge-base scopes
- C. Unified mechanism but limited coverage—a unified data-access permission-control mechanism has been established that can restrict the data scope accessible to AI applications/agents, but some scenarios or data assets are not yet under control
- D. Complete and full coverage—the data-access permissions of all AI applications/agents are governed by a unified mechanism supporting fine-grained access boundaries down to tables, fields, and knowledge-base partitions, with a queryable data-access audit record kept
- N/A. Not applicable—the enterprise currently has no scenario where AI agents or automated programs access data

## 3.2 Observability of the Data-Supply Chain

### Q3
**Q3. Is there a unified view to see, for each AI scenario, the latency and success rate of obtaining data from the data platform, as well as the data-side costs (e.g. storage, compute, retrieval call volume)?**

- A. No unified view—the data-consumption performance of each AI scenario (latency, success rate) is scattered across their own system logs, requiring case-by-case investigation, with no way to grasp the whole picture
- B. Partially aggregated—a few key metrics (e.g. overall call volume) can be seen on a dashboard, but metrics such as data latency and data-side cost are missing or scattered
- C. Basically unified—a unified view covers the data-fetch latency, success rate, and main data-side cost metrics of most AI scenarios, but some scenarios or cost items still need to be investigated separately
- D. Fully unified and observable—the data-fetch performance of all AI scenarios (latency, success rate, data-side cost) can be viewed in a unified view, supporting drill-down analysis by scenario and cross-scenario comparison
- N/A. Not applicable—the enterprise currently has too few AI scenarios, so there is no need for unified cross-scenario observation

### Q4
**Q4. Is the quality of retrieval or knowledge-base recall (e.g. whether recall is accurate and relevance is up to standard) continuously monitored, rather than untracked once it goes live?**

- A. Not tracked after launch—retrieval or recall effectiveness is not continuously monitored after launch; whether it is accurate is sensed mainly through sporadic business-side feedback
- B. Occasional manual evaluation—manual sampling checks of recall effectiveness have been done at irregular intervals, but there is no continuous, automated monitoring
- C. Monitored but not comprehensive—continuous monitoring of recall quality has been established for some scenarios (e.g. tracking relevance-score trends), but it does not cover all AI scenarios that depend on retrieval/recall
- D. Continuously monitored and comparable—the retrieval/recall quality of each AI scenario is continuously monitored, different scenarios' performance can be compared at the platform level, and a clear quality drop can proactively trigger an alert
- N/A. Not applicable—the enterprise currently has no AI scenarios that depend on retrieval or recall capabilities

## 3.3 Capacity Planning and Elasticity of Data Supply

### Q5
**Q5. Is the capacity planning of data services (feature serving, retrieval, knowledge-base queries, etc.) based on actual data scale and call volume, rather than a "good enough to run" experiential estimate?**

- A. Experiential estimate—the resource configuration for data services relies on a "should be enough" judgment from experience, without any calculation based on actual data scale and call volume
- B. Preliminary estimate—the data scale and expected call volume have been roughly estimated, but no validation has been done against real response-time requirements
- C. Based on measurement—capacity planning comprehensively considers data scale, call volume (QPS), and response-time requirements, and at least one load test has been done to verify sufficiency
- D. Continuously optimized—there is a complete capacity-planning mechanism that recalculates on a fixed cadence based on actual call data and expands data-service capacity ahead of time in line with business-growth forecasts
- N/A. Not applicable—the enterprise currently has no dedicated data service provided for AI scenarios

### Q6
**Q6. Does the data platform support automatic scaling in response to fluctuations in AI call volume, with observable records kept of the scaling actions?**

- A. Fixed resources—the data-service resource configuration is fixed and cannot auto-adjust to fluctuations in AI call volume; at peak times only manual, ad-hoc intervention is possible
- B. Manual scaling—scaling is possible but requires manual operation, usually a passive response after a problem has already appeared, taking a long time to handle
- C. Partially automated—some components of the data service (e.g. compute resources) support auto-scaling, but core data-storage or retrieval components still require manual adjustment
- D. Fully automated—the main components of the data service all support auto-scaling, the scaling policy is explicit, and every scaling action can be queried as a record in the monitoring system
- N/A. Not applicable—the enterprise's AI scenarios call the data at a small or stable volume, so elastic scaling is not yet needed

## 3.4 Impact Assessment of Data Changes and Failure Recovery

### Q7
**Q7. Before major changes on the data-platform side (e.g. replacing the data-processing engine, adjusting the data-warehouse/lakehouse architecture, switching the feature store or vector store, upgrading the data-integration tool), is the scope of impact on downstream AI scenarios assessed?**

- A. Change directly—the data-platform change is executed directly, and only afterward is it discovered which downstream AI scenarios were affected and how
- B. Aware but no systematic assessment—it is known that data-platform changes affect downstream AI scenarios, but before the change no systematic inventory of the specific affected data assets and scenarios is made
- C. Impact-scope assessment done—before the change, the affected data assets (tables, pipelines, features, indexes, etc.) and the downstream AI-scenario list are inventoried, and effectiveness or performance comparisons are done for key scenarios; only if they pass is launch allowed
- D. Complete impact-assessment process—beyond impact-scope inventory and effectiveness comparison, the time cost of data migration or recomputation is also assessed, forming a standardized pre-change checklist that is strictly executed
- N/A. Not applicable—the enterprise's data-platform architecture is basically stable, with no related major changes recently

### Q8
**Q8. Do data-platform architecture changes have an explicit change-impact list and a clear rollback plan?**

- A. None—data-platform changes lack a formal impact assessment and rollback plan, dealt with ad hoc after problems occur
- B. Basic plan—there is a rollback plan but it is not detailed enough; which data assets and AI scenarios are involved is judged mainly from experience rather than a systematic list
- C. List and plan in place—there is a change-impact list (explicitly stating which data assets, which AI scenarios and downstream consumers are involved) and a written rollback plan, but it has not been validated through an actual drill
- D. Complete and validated—the change-impact list is detailed, the rollback plan is explicit and validated through at least one drill, and the choice of change window and the notification mechanism for downstream consumers are standardized
- N/A. Not applicable—the enterprise's data-platform architecture is basically stable, with no related major changes recently

### Q9
**Q9. When a key component of the data platform (data pipeline, storage, index, feature service, etc.) fails, is there a mechanism to automatically switch to or roll back to a stable data version?**

- A. Fully manual—when any component of the data platform fails, recovery relies entirely on manual investigation and manual operation, and the time needed to stop the bleeding is uncontrollable
- B. Partially automated—there are basic fault-tolerance mechanisms (e.g. automatic retry on task failure), but the core recovery actions involving data-version switching or rollback still require manual judgment and operation
- C. Key components automated—the core data components supporting key AI scenarios (e.g. main data pipelines, core indexes) have automatic switch or rollback mechanisms, but coverage is limited
- D. Fully automated—the main components of the data platform all support automatic switching or rollback to the last stable data version on failure, and failures can usually stop the bleeding automatically within minutes
- N/A. Not applicable—the enterprise's AI scenarios are small in scale and no failure requiring automatic data-platform switch or rollback has occurred yet

### Q10
**Q10. Before a major data-platform change goes live, has a stress test or effectiveness validation been done for the affected key AI scenarios?**

- A. No validation—data-platform changes go live directly, and actual effectiveness is judged only after business-side feedback
- B. Occasional validation—the capability to validate technically exists, but it has not become a routine process; whether validation is done depends on the specific project and the judgment of the people involved
- C. Regular validation—before a major data-platform change goes live, there is a regular or institutionalized stress-test / effectiveness-validation mechanism to assess the risk to downstream AI scenarios
- D. Routine and automated—validation of data-platform changes is integrated into the release process; a major change automatically triggers a regression check of downstream AI scenarios, and the result serves as the basis for the go-live decision
- N/A. Not applicable—the enterprise currently has no key data-platform components requiring pre-change validation

## 3.5 Intelligent Operations and Inspection of the Data Platform

### Q11
**Q11. Has AI-assisted anomaly detection been introduced into the data platform's performance monitoring (e.g. automatically identifying abnormal patterns in metrics such as data-pipeline latency, throughput, and resource usage)?**

- A. Not introduced—the data platform's performance monitoring is entirely based on static-threshold alerts, with no AI/ML-assisted anomaly detection
- B. Preliminary exploration—AI anomaly detection has been trialed on some data pipelines or components, but it is not yet deployed at scale and its effectiveness is unstable
- C. Partially deployed—AI anomaly detection has been introduced into the performance monitoring of core data components supporting key AI scenarios, able to identify performance-anomaly patterns hard to find with static thresholds, shortening problem-discovery time
- D. Applied at scale—AI anomaly detection covers the main performance metrics of the data platform, can automatically correlate multi-dimensional data such as latency, throughput, and resource usage for combined judgment, and continuously tracks and optimizes detection accuracy
- N/A. Not applicable—the enterprise's data-platform performance-monitoring system is not yet established

### Q12
**Q12. Has AI-assisted anomaly detection been introduced into data-quality monitoring (e.g. automatically identifying data-distribution drift, outlier patterns, and unusual fluctuations in quality metrics), coupled with corresponding automated remediation actions?**

- A. Not introduced—data-quality monitoring relies entirely on preset static rules (e.g. fixed thresholds), with no AI assistance to identify complex or undefined anomaly patterns, and problems can only be handled manually after they occur
- B. Preliminary exploration—AI or statistical models have been tried to identify anomalies in data distribution or quality metrics, but they do not yet run stably and problem handling still relies entirely on humans once found
- C. Partially deployed—AI anomaly detection has been introduced into the quality monitoring of key data assets, with automated remediation actions equipped for some common problems (e.g. pipeline-task retry, isolation of clearly anomalous data)
- D. Applied at scale—AI anomaly detection covers the quality monitoring of the main data assets on the platform, can automatically identify multiple anomaly patterns, and automatically executes predefined remediation actions for common problems (rerun the pipeline, isolate the anomalous source, switch to a stable data version, etc.), with humans only handling complex or unknown problems
- N/A. Not applicable—the enterprise currently has no quantitative data-quality monitoring system in place
