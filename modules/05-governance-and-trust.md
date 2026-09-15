---
id: dim5
title: Governance & Trust
dimension_number: 5
question_count: 5
---

This dimension assesses whether the enterprise has established **unified data-governance standards** so that the same piece of core data follows one set of definitions, calculation rules, and quality rules—whether it is consumed by AI scenarios, analyzed by humans, or served externally—rather than "every system telling its own story."

## 5.1 Core Data and Unified Standards

### Q1
**Q1. Has the enterprise explicitly defined which data belongs to "core governed data" (e.g. master data such as customers, products, contracts, finance), and designated an authoritative source system for each type of data?**

- A. Not defined—there is no clarity on which data is core governed data, and multiple systems may each be treated as the "accurate version"
- B. Preliminarily identified—some core data (e.g. customers, products) has been identified, but the authoritative source system has not reached consensus across all teams
- C. Defined and designated—core data is clearly classified, most core-data categories have a designated authoritative source system, and this is published in documentation
- D. Institutionalized execution—core data and authoritative sources have institutionalized definitions, all consumers are mandated to fetch data from the authoritative source, and violations are monitored and corrected
- N/A. Not applicable—the enterprise's data is currently small in scale and has not yet reached the complexity that requires distinguishing "core governed data"

### Q2
**Q2. Have the definitions, naming, and calculation rules of this core data been documented and published as a unified standard?**

- A. Each has its own understanding—the definitions and calculation rules of core data are interpreted by each team on its own, with no unified standard
- B. Partial documentation—some data has definition documents, but they are incomplete or not all teams know to reference them
- C. Unified publication—the definitions, naming, and calculation rules of core data are documented and published uniformly for all consumers to reference, but there is no technical constraint mandating reference
- D. Published and mandatorily followed—the unified standard is published and embedded in the technical implementation (e.g. a semantic layer, a metrics platform), so consumers automatically use the standard definitions and cannot "redefine" on their own
- N/A. Not applicable—the enterprise has not yet identified core data requiring unified definitions

## 5.2 Mandatory Use of the Governed Source

### Q3
**Q3. When an AI scenario needs to use core data, is it mandatory to fetch data from the governed authoritative data source, with bypassing the governance chain disallowed?**

- A. Not mandatory—AI scenarios can directly connect to any data source, including the raw system, a local copy, or a non-authoritative source
- B. Recommended but not mandatory—there is guidance recommending fetching from the authoritative source, but bypassing is not technically prevented, and bypassing does occur in practice
- C. Mostly mandatory—most core AI scenarios are forced to fetch data through the governance chain, but some edge scenarios or newly launched scenarios may not be fully covered
- D. Fully mandatory—all AI scenarios must fetch data from the governed authoritative source, access control is technically guaranteed, and bypassing can be detected and blocked
- N/A. Not applicable—the enterprise currently has no AI scenarios that consume core governed data

### Q4
**Q4. Do the externally provided data services and the internal AI scenarios use the same set of governed data and the same set of metric definitions?**

- A. Maintained separately—the data and definitions used by external services and internal AI are maintained separately, with a risk of inconsistency
- B. Aware but not unified—it is known that they should be consistent, but the technical implementation uses different chains for external and internal, so occasional data inconsistency occurs
- C. Basically unified—core data and main metrics use the same data source and definitions for both external and internal use, but some sub-metrics may differ
- D. Fully unified—the data and metric definitions for external and internal use are fully unified, consistency is guaranteed through a unified data-service layer, and there is a monitoring/validation mechanism
- N/A. Not applicable—the enterprise currently has no externally provided data services (e.g. a customer portal, an open API)

## 5.3 Standard Change and Version Management

### Q5
**Q5. Once a change occurs to the governance standard of core data, is there an explicit version-management and notification mechanism?**

- A. Changed with no one knowing—after the governance standard changes, there is no unified notification mechanism, so consumers may keep using the old standard unaware
- B. Notification but not systematic—changes are communicated to some stakeholders by email or meeting, but coverage is incomplete and there is no version management
- C. Version management and notification in place—the governance standard has version numbers, and changes have a formal notification process covering the main consumers, but it does not guarantee that all consumers have adapted
- D. Closed-loop management—the standard is version-managed, changes automatically notify all consumers, and there is a validation mechanism to confirm each party (including AI scenarios) has completed adaptation
- N/A. Not applicable—the enterprise's core-data governance standard has not changed since it was established
