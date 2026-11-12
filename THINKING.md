# BiztelAI Assignment: Technical & Strategic Thinking Document

**Author**: Vishwajeet  
**Project**: Shop Floor SOP & Maintenance Copilot  
**Plant**: Kaveri Precision Components Pvt. Ltd. (Hosur Plant)  
**Date**: November 2026  

---

## 1. Understand the User

### 1.1 Who is the Supervisor?
On the shop floor of Kaveri Precision Components (Hosur Plant), the primary user is a **Shift Production / Quality Control (QC) Supervisor** (e.g., Ramesh or Divya). They oversee high-speed CNC turning centres (`TX-200`, machines CNC-04 to CNC-09), coordinate receiving inspection at Stores Bay 3, and enforce strict safety standards across 20+ line operators and maintenance technicians during 8-hour rotating shifts.

### 1.2 Operating Environment & Context
* **Physical Realities**: Fast-paced, high-decibel machine shop with coolant mist, grease, chip conveyors, and physical barriers. Supervisors are constantly on their feet, wearing safety glasses, steel-toed boots, and often industrial gloves.
* **Device Form Factor**: They do not sit at desks with desktop monitors; they carry a company-issued mobile phone or ruggedized tablet across machine bays. Wi-Fi can be patchy behind heavy steel CNC machine enclosures.
* **Cognitive Load**: Supervisors make dozens of quick tactical decisions under intense throughput pressure (keeping cycle times down and avoiding line stops) while carrying strict legal and quality responsibility for ISO 9001 compliance and zero-harm workplace safety (OSHA / LOTO).

### 1.3 Key Objectives
1. **Minimize CNC Downtime**: Rapidly troubleshoot unexpected machine alarms (e.g., `AL-104` way lube low, `AL-101` hydraulic pressure drop) without waiting 30 minutes for a maintenance engineer.
2. **Ensure First-Time-Right Quality**: Prevent non-conforming bought-out parts (such as `BH-220` bearing housings) from entering the assembly line by adhering strictly to sampling plans and critical dimension tolerances.
3. **Enforce Absolute Zero-Energy Safety**: Execute lockout/tagout (LOTO) protocols flawlessly. Ensure unauthorized lock removals never occur, as an unexpected machine startup can cause severe injury or fatality.

### 1.4 Frustrations & Pain Points Today
* **The "Revision Trap" (Obsolete Procedures)**: Plants regularly update SOPs (e.g., `QC-SOP-014` transitioning from Rev 03 to Rev 04). In practice, laminated physical printouts of Rev 03 remain taped near Gate 2 or in desk drawers. Following outdated instructions (e.g., inspecting 5 random samples instead of 13 for a lot of 200, or routing rejects to the old Gate 2 red bin instead of Quarantine Cage Q1) leads to customer rejections and audit non-conformances.
* **Time-Consuming Document Traversal**: Finding an alarm code or bolt torque in an 80-page binder or a slow, unindexed PDF portal takes 10–15 minutes while a CNC turning centre sits idle.
* **Typing Friction**: Typing complex technical queries with greasy fingers or while wearing nitrile/work gloves on a small mobile touchscreen is frustrating.
* **Fear of AI Hallucinations**: In manufacturing, an AI that politely fabricates a torque value (e.g., guessing 150 Nm instead of 110 Nm) will snap a spindle bolt or ruin a chuck. The supervisor needs absolute fidelity to verified plant manuals.

### 1.5 Stated Assumptions
1. Supervisors have basic mobile literacy (using WhatsApp, internal QMS mobile web apps).
2. The plant has local intranet Wi-Fi coverage across the machining and stores bays.
3. Documents indexed are authoritative, signed QMS PDF documents.

---

## 2. User Journey (Initial Draft - Pre-AI Challenge)

```
[Trigger on Shop Floor] ──> [Mobile Query] ──> [RAG Retrieval] ──> [Actionable Answer + Citation] ──> [Line Resumes]
```

### Step 1: Trigger
* *Scenario A*: CNC-06 trips mid-cycle with flashing amber beacon showing **Alarm AL-104**.
* *Scenario B*: A batch of 200 machined `BH-220` bearing housings arrives at Receiving Stores Bay 3.
* *Scenario C*: A maintenance contractor left the plant on Friday evening with their red padlock still on the main 415V electrical isolator of CNC-04.

### Step 2: Access & Query
* The supervisor pulls out their smartphone, taps the Copilot icon on the browser, and either speaks via microphone (*"AL-104 on TX-200 what to do"*) or types a short phrase (*"AL-104"* or *"BH-220 OD tolerance"*).

### Step 3: Processing & Retrieval
* The system parses the question, identifies domain entities (`AL-104`, `TX-200`, `BH-220`), retrieves the exact section chunk from the indexed PDF corpus, and prioritizes the active revision.

### Step 4: Output & Verification
* The app renders:
  1. **Direct Operational Action**: Bulleted parameters (e.g., *"Top up with ISO VG 68 oil to MAX mark, press RESET"*).
  2. **Verifiable Source Citation**: Document name, revision, section, and page number (`MNT-MAN-CNC-02 Rev 02, Section 6, Page 2`).
  3. **Revision Freshness Status**: A badge confirming the document is the active release.

### Step 5: Execution
* The supervisor tops up the way lube reservoir, resets the CNC controller, confirms normal cycle restart, and logs the action. Total elapsed time: 90 seconds.

### What Could Go Wrong?
1. **Outdated SOP Match**: The RAG engine might match Rev 03 instead of Rev 04 if the user query matches generic text in the older revision.
2. **Ambiguity / Incomplete Guidance**: An alarm could have multiple root causes not captured in the table.
3. **Hallucination on Missing Specs**: If an operator asks for something not in the SOPs (e.g., *"aluminum feed rate"*), standard LLMs guess numbers, which could crash the cutting tool.
4. **Network Drop**: Loss of Wi-Fi behind metal enclosures could cause blank screens or hanging spinners.

---

## 3. AI Challenge: Skeptical Product Manager & Auditor Critique

To pressure-test this user journey, we simulated a rigorous critique from a skeptical Manufacturing Product Manager & Lead ISO 9001 Auditor.

### Conversation Excerpts

> **Skeptical PM**: *"Your user journey assumes the supervisor writes polite, grammatically complete questions like 'What is the recommended coolant concentration for the TX-200?'. In reality, an operator is yelling across the line, coolant is spraying, and the supervisor types 'AL104' or 'coolant' or 'lockout absent'. If your RAG requires sentence-level semantic similarity, it will fail on raw keyword tokens."*

> **Lead Auditor**: *"In my audits at automotive component plants, 30% of major findings come from using superseded documentation. You have both Rev 03 and Rev 04 of `QC-SOP-014` in your folder. Rev 03 says 5 samples for any lot and put rejects in the red bin near Gate 2. Rev 04 says 13 samples for lot of 200 and put rejects in Quarantine Cage Q1. If your AI answers with Rev 03, the company fails their audit and ships defective parts. How does your app prevent this disaster?"*

> **Skeptical PM**: *"What happens when someone asks a dangerous question not covered in the PDF, like 'Can I bypass the interlock switch to blow chips?' If your system generates a polite, speculative LLM reply, someone loses an arm. The app must have zero hallucination tolerance."*

### Reflection: What We Agreed With, Disagreed With, and Changed

#### What We Agreed With:
1. **Supervisors Type in Shorthand**: Keyword queries (`AL-104`, `BH-220`, `110 Nm`) must match with high precision. Standard dense embeddings often dilute rare alphanumeric codes; hybrid BM25 + exact-entity boosting is required.
2. **Document Obsolescence is a Critical Risk**: In manufacturing, document versioning cannot be treated as just generic text chunks. The system must know which document is active and which is superseded, boosting the active revision and aggressively flagging any reference to obsolete versions.
3. **Strict Grounding / Zero-Hallucination Guardrail**: When a topic is absent from the documents, the model must immediately refuse with a clear *"Not found in documents"* alert rather than attempting to interpolate.

#### What We Disagreed With:
* The PM suggested removing generative natural language completely and only dumping raw PDF image cutouts. We disagreed: raw PDF tables on a 6-inch phone screen require pinching, zooming, and scrolling through dense rows in poor shop floor lighting. Extracting the **exact bold metric** (e.g. `90.000 mm +/- 0.050 mm`) alongside an expandable citation gives the supervisor instant clarity.

#### What We Changed in the Implementation:
1. **Added Revision-Aware Freshness Engine**: The RAG indexer automatically detects document revision relationships (e.g., `QC-SOP-014 Rev 04` superseding `Rev 03`), prioritizes the active release, and displays a prominent **Revision Freshness Status Banner** on every query.
2. **Hard Out-of-Scope Guardrails**: Configured strict confidence scoring and negative intent detection so unanswerable questions (e.g., aluminum feed rates) trigger a clear refusal state.
3. **Simplified Minimalist UI**: Following user feedback, eliminated cluttered chips and complex menus down to a clean, focused search bar and high-contrast answer box with source badges.

---

## 4. The Improvement Added & Why We Chose It

### The Improvement: **Revision-Aware Freshness & Superseded SOP Alert Engine**

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RAG Ingestion Pipeline                          │
│                                                                        │
│   QC-SOP-014 Rev 03 (Old) ──┐                                          │
│                             ├──> Revision Parser ──> Active: Rev 04    │
│   QC-SOP-014 Rev 04 (New) ──┘                        Superseded: Rev 03 │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Query Scoring Engine                            │
│                                                                        │
│  - Active Documents: +25% Score Boost                                  │
│  - Superseded Documents: 60% Penalty (unless explicitly requested)     │
│  - UI Banner: "✓ Verified against latest active release: Rev 04"       │
│               OR "⚠️ Warning: Document is SUPERSEDED by Rev 04"         │
└────────────────────────────────────────────────────────────────────────┘
```

### Why We Chose It:
1. **Direct Alignment with Manufacturing Realities**: In precision manufacturing (ISO 9001, IATF 16949), operating on obsolete procedures is one of the most common causes of scrap and audit penalties.
   - Under `Rev 03`: An inspector would draw 5 samples for a lot of 500 and dump rejects into a bin near Gate 2.
   - Under `Rev 04`: The inspector must draw 13 samples and lock rejects in Quarantine Cage Q1 (Stores Bay 3), with key custody under the Shift QC Supervisor.
2. **Transparent Audit Trail**: Showing the supervisor whether the retrieved guidance comes from the active release provides instant confidence without having to walk back to the QC office to check the master document register.

---

## 5. Final Reflection

### 5.1 What We Would Build Next
1. **Multimodal Visual Diagnostics (Camera Integration)**: Allow a supervisor to snap a photo of a worn tool insert, chipped bearing race, or alarm screen. The vision model would cross-reference the visual damage against inspection photo criteria in the manual.
2. **ERP / QMS Bi-Directional Integration**: When an alarm like `AL-104` or an incoming lot rejection occurs, provide a one-click button to automatically raise an e-Work Order in SAP/Infor or trigger a SCAR (Supplier Corrective Action Request) directly in the plant's QMS app as required by `QC-SOP-014 Section 5.9`.
3. **Offline Progressive Web App (PWA) with Local Embeddings**: Cache critical emergency SOPs (LOTO `SAF-SOP-003`, emergency shutdowns) locally in browser IndexedDB with on-device small model inference, ensuring 100% uptime even in metal-shielded basement bays without Wi-Fi.

### 5.2 What We Are Unsure About
* **Acoustic Noise Limits on Voice Input**: While the Web Speech API works smoothly in office settings, real machine shops often register 80–85 dB(A) background noise from coolant pumps and chip augers. Field testing with noise-canceling bone-conduction headsets is required to verify real-world voice recognition accuracy.
* **Granularity of Multi-Part Queries**: If a supervisor asks *"Check coolant and tell me chuck bolt torque"*, multi-document RAG needs to synthesize across `MNT-MAN-CNC-02` Section 3 and Section 5 without dropping critical parameters.

### 5.3 What We Would Ask the Customer
1. *"How often are SOPs revised, and do you currently maintain a centralized digital QMS (e.g. MasterControl, ETQ, SharePoint) with an API, or are revisions managed manually?"*
2. *"What are the top 10 machine alarm codes or line bottlenecks that cause 80% of your unscheduled downtime today?"*
3. *"Do line operators speak English exclusively, or would Tamil/Kannada/Hindi voice input and translation accelerate adoption on the shop floor?"*
4. *"Are supervisors allowed to carry personal smartphones on the floor, or must the solution be locked to plant-managed ruggedized mobile devices?"*

### 5.4 Challenges Faced & How We Handled Them

| Challenge Faced | Root Cause | Resolution |
| :--- | :--- | :--- |
| **Cross-Page Section Splitting** | Section 6 of `MNT-MAN-CNC-02` started at the bottom of Page 1 (`AL-101`) and continued onto Page 2 (`AL-104`, `AL-210`, etc.). A naive page-by-page chunker clipped `AL-104`. | Built a **cross-page document stitcher with page-boundary tracking**. All sections remain completely intact regardless of page breaks. |
| **Starlette TemplateResponse API Breakage** | Starlette updated its signature in recent releases to `TemplateResponse(request, name, context)`, causing `TypeError: unhashable type: 'dict'` when called positionally. | Updated to explicit keyword arguments `TemplateResponse(request=request, name="index.html", context={...})`, ensuring full backward and forward compatibility. |
| **Zero-Hallucination Out-of-Scope Queries** | Pure vector embeddings return nearest neighbors even for irrelevant queries (e.g., cutting aluminum feed rates). | Implemented **hybrid keyword + BM25 scoring with a strict confidence threshold and domain intent filter**. Out-of-scope queries immediately return the grounded refusal message. |
| **Local Wi-Fi Network Binding** | Windows local socket binding required proper host configuration (`0.0.0.0`) and automated local IP detection (`10.194.167.218`) for mobile access. | Dynamically detect local network IP via UDP socket probe and host on `0.0.0.0:8000`, enabling zero-configuration phone testing. |
