---
id: dim6
title: Security & Compliance
dimension_number: 6
question_count: 5
---

This dimension assesses whether the enterprise has **fully brought AI-related data processing, agent invocation, and scenario operation into its existing security and governance system**—through classifying and pre-protecting sensitive data, applying identity authentication and audit controls to AI/agent access chains on par with human users, and identifying and providing basic protection against new attack surfaces such as prompt injection, data poisoning, and Shadow AI—thereby building a provable, traceable, continuously improvable risk-control closed loop, so that AI can run stably within the existing security and compliance boundaries rather than drifting outside the traditional defenses.

## 6.1 Sensitive-Data Classification and Pre-Protection

### Q1
**Q1. For sources involving PII or other sensitive data, is there an automated classification and masking/tagging process before they enter the AI pipeline?**

- A. Used directly—sensitive data (including PII) enters the AI pipeline (training, embedding, RAG corpus, etc.) directly, with no upfront classification or masking
- B. Manual review—the handling of sensitive data relies on manual review and manual masking, with coverage and consistency hard to guarantee
- C. Partially automated—there are automated sensitive-data identification and masking tools that cover most, but not all, data sources entering the AI pipeline
- D. Fully automated—all data entering the AI pipeline undergoes automated classification and masking/tagging, covering training, embedding, RAG, and agent-invocation scenarios
- N/A. Not applicable—the enterprise's AI pipeline currently involves no PII or other sensitive data

### Q2
**Q2. Does the data classification and grading tagging system cover all data assets consumed by AI scenarios, and does it play a real role in access control and masking policies?**

- A. Not covered—classification and grading cover only traditional reports or applications; the data assets consumed by AI are outside the tagging system
- B. Partially covered—some data used by AI scenarios has classification/grading tags, but coverage is incomplete and the tags play no role in access control
- C. Basically covered—most AI-consumed data has been brought into the classification/grading system, and the tags play a real role in access control and masking policies
- D. Fully covered and enforced—all AI-consumed data assets have classification/grading tags, the tags drive automatic execution of access-control and masking policies, and tag accuracy is audited on a fixed cadence
- N/A. Not applicable—the enterprise currently has no data classification and grading tagging system

## 6.2 Identity and Least Privilege on AI Access Paths

### Q3
**Q3. Do the identity, permission assignment, and access-chain controls of AI agents follow the principle of least privilege, on par with the security controls of human users?**

- A. Over-broad permissions and missing controls—agents use human accounts or high-privilege service accounts, with an access scope far exceeding what the task requires; and call chains such as agent-to-database and agent-to-external-API are not brought into encryption and access auditing, with a control level clearly lower than for human users
- B. Basic restrictions, but controls not yet at parity—agents have their own identity, but the permission granularity is coarse (e.g. whole-database access) and not strictly minimized to task needs; only some nodes of the call chain (e.g. agent-to-database) have basic encryption and access control, while the rest (e.g. model-to-vector-store, agent-to-external-API) remain blank
- C. Least privilege, with controls broadly at parity—agent permissions are minimized and assigned by task need, with a dedicated identity and fine-grained access control; the encryption and access control of the main call chains are basically on par with human users
- D. Least privilege + periodic review + full-chain auditing at parity—least privilege is strictly enforced, agent permissions are reviewed on a fixed cadence for continued reasonableness, and expired or no-longer-needed permissions are revoked; all AI call paths (including service accounts and internal model chains) apply the same encryption and access-control policies as human users, with complete audit logs
- N/A. Not applicable—the enterprise currently uses no AI agents with an independent identity or tool-calling capability

## 6.3 Incident Response and AI-Specific Attack Surfaces

### Q4
**Q4. Has the security-incident-response SOP been updated to bring AI/agent-related identity tracking, session logs, and tool-invocation records into the standard process?**

- A. Not incorporated—the security-incident SOP still centers on traditional applications and does not consider AI/agent identity tracking and session logs
- B. Aware but not implemented—it is known that AI-related chains need to be incorporated, but the SOP has not been updated, so ad-hoc investigation is relied upon when incidents actually occur
- C. SOP updated—the security-incident SOP now incorporates agent identity tracking, session logs, and tool-invocation records, so there is a standard process to follow when incidents occur
- D. Complete and validated—the SOP is complete and has been drilled at least once, able to clarify within a defined time window "which agent, under what identity, accessed what data," supporting rapid isolation and rollback
- N/A. Not applicable—the enterprise currently has no dedicated security-incident-response SOP system, or no AI/agent-related access chains

### Q5
**Q5. For AI-specific attack surfaces such as prompt injection and data poisoning, has at least one assessment or red-team exercise been done?**

- A. Never done—no assessment or protection has been done for AI-specific attack surfaces; the focus is still on traditional web security
- B. Preliminary awareness—the team is aware of AI-specific risks (e.g. prompt injection), but no formal assessment or exercise has been done
- C. Assessment done—at least one assessment or red-team exercise targeting the AI attack surface has been done, and basic protective measures have been established accordingly
- D. Continuous protection—AI security assessments/red-team exercises are conducted on a fixed cadence, there is a complete protection system (input sanitization, source tagging, permission isolation, output monitoring), and it is continuously iterated
- N/A. Not applicable—the enterprise currently has no AI application scenarios that are externally exposed or at risk of attack
