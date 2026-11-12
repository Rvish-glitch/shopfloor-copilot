# BiztelAI Shop Floor Copilot

An intelligent, grounded SOP and Maintenance Copilot designed for manufacturing supervisors and technicians at **Kaveri Precision Components Pvt. Ltd. (Hosur Plant)**.

Built with **FastAPI**, **BM25 Hybrid Retrieval**, **Section-Aware Semantic Chunking**, and an **Active-Revision Freshness Engine**.

---

## 🚀 Quickstart

### 1. Prerequisites
* Python 3.10+ (tested on Python 3.12)
* Google Chrome, Safari, or any modern web browser

### 2. Installation
```bash
# Clone the repository
git clone <your-repo-link>
cd biztel

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Copilot
To make the application accessible both on your laptop and from any phone/tablet on the same Wi-Fi network:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8505
```

* **Laptop Browser**: Open [http://localhost:8505](http://localhost:8505)
* **Phone / Tablet**: Open `http://<YOUR_LOCAL_IP>:8505` (e.g. `http://10.194.167.218:8505`)

---

## 🎯 Key Capabilities & Architecture

1. **Clean, Focused Shop Floor UX**: Streamlined input box and instant answer card with zero clutter, designed for fast lookups on mobile or tablet devices.
2. **Revision-Aware Freshness Engine (Our Improvement)**:
   - Automatically detects superseding relationships (`QC-SOP-014 Rev 04` supersedes `Rev 03`).
   - Prioritizes the active release with a `+25%` relevance boost and penalizes obsolete revisions.
   - Surfaces a visible status banner confirming active release validity or warning if an older procedure is referenced.
3. **Zero-Hallucination Guardrail**:
   - Queries outside the scope of plant SOPs (e.g., cutting feeds/speeds) return a clear refusal state: *"Not found in documents."*
4. **Hands-Free Voice Input**:
   - Built-in microphone button (via Web Speech API) allowing supervisors wearing gloves or with dirty hands to speak queries naturally.
5. **Multi-Provider LLM Integration**:
   - Built-in **Shop-Floor Deterministic Extractor** (zero external API keys required, works 100% offline).
   - Optional hosted LLM support for OpenAI (`gpt-4o-mini`), Google Gemini (`gemini-2.5-flash`), or local Ollama via `.env`.

---

## 📋 Evaluation Questions & Copilot Answers

### Sample Questions from Assignment
| # | Question | Copilot Answer & Citation |
|---|:---|:---|
| **1** | *What is the recommended coolant concentration for the TX-200 CNC turning centre?* | **6 - 8 %** (Refractometer reading × 1.0 factor). Checked weekly by the machine Operator.<br>*(Source: `MNT-MAN-CNC-02 Rev 02`, Section 3 & 4, Page 1)* |
| **2** | *The machine is showing alarm AL-104. What does it mean and what should the operator do?* | **Meaning**: Way lube oil level low.<br>**Action**: Top up with ISO VG 68 oil to the MAX mark, then press RESET. Machine can continue after reset.<br>*(Source: `MNT-MAN-CNC-02 Rev 02`, Section 6, Page 2)* |
| **3** | *Who is allowed to remove a lockout lock from a machine?* | Each authorised person removes **only their own lock**. Nobody may remove another person's lock.<br>*Absentee rule*: If owner has left the plant, removal requires joint authorization from **both Production Manager and Safety Officer** (Section 6).<br>*(Source: `SAF-SOP-003 Rev 05`, Section 5 & 6, Page 1)* |
| **4** | *What is the outer diameter tolerance for the BH-220 bearing housing?* | Nominal: **90.000 mm**, Tolerance: **+/- 0.050 mm** (Range: 89.950 mm to 90.050 mm). Checked with digital caliper. Defect class: Major.<br>*(Source: `QC-SOP-014 Rev 04`, Section 6, Page 2)* |
| **5** | *How often should spindle runout be checked, and who does it?* | Checked **Monthly** by the **Maintenance technician** (limit: 0.005 mm max at chuck face using dial indicator).<br>*(Source: `MNT-MAN-CNC-02 Rev 02`, Section 3 & 4, Page 1)* |

---

### Our 5 Custom Test Questions (Including Unanswerable Question)

| # | Custom Test Question | Type | Copilot Answer & Citation |
|---|:---|:---|:---|
| **1** | *Where should rejected incoming material be moved, and who keeps the key?* | **Revision Check (Rev 04 vs 03)** | Tagged with a **RED tag** and moved to **Quarantine Cage Q1, Stores Bay 3**. The cage is locked; the key is held by the **Shift QC Supervisor**. Supervisor informs SQE within 4 hours to raise SCAR. Form QF-07A.<br>*(Source: `QC-SOP-014 Rev 04`, Section 5 & 8, Page 2)* |
| **2** | *What torque and tightening pattern should be used when re-mounting the chuck on the TX-200 CNC?* | **Mechanical PM** | Tighten mounting bolts in a **criss-cross sequence** to **110 Nm** using a calibrated torque wrench.<br>*(Source: `MNT-MAN-CNC-02 Rev 02`, Section 5, Page 1)* |
| **3** | *If a lot of 200 bought-out components arrives at receiving, how many samples must be inspected, and when is the lot rejected?* | **Sampling Plan** | For lot size 91 - 500 pieces: inspect **13 samples**. Accept if minor defects are **0**, reject if minor defects are **1 or more** (or if any single critical or major defect is found).<br>*(Source: `QC-SOP-014 Rev 04`, Section 4, Page 1)* |
| **4** | *What steps must be followed if an operator leaves the plant with their lockout lock still attached?* | **Emergency LOTO Escalation** | 1. Attempt contact by phone. 2. If unreachable, **both Production Manager and Safety Officer** must authorise removal. 3. Physical inspection confirms safe to re-energise. 4. Record on form **SF-12 Lock Removal Record**. 5. Inform owner before next shift.<br>*(Source: `SAF-SOP-003 Rev 05`, Section 6, Page 1-2)* |
| **5** | *What is the recommended feed rate and spindle speed for cutting aluminium on the TX-200?* | **Out-of-Scope (Unanswerable)** | **Not found in documents.** The provided plant SOPs and manuals do not contain information regarding this request. Please check with your Shift Supervisor, Maintenance Manager, or refer to the machine's OEM operations manual and CAM programming sheets. |

---

## 🧪 Automated Testing

The repository includes a comprehensive `pytest` test suite verifying all document extractions, entity matching, revision priority, and out-of-scope guardrails:

```bash
python -m pytest tests/ -v
```

All 11 unit and integration tests pass with 100% reliability.

---

## 🐳 Docker Deployment (Bonus)

To run in a containerized environment:

```bash
# Build and run with Docker Compose
docker-compose up --build
```
Access at `http://localhost:8000`.

---

## 📂 Project Structure

```
biztel/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI endpoints, CORS, network IP detection
│   ├── rag.py               # Document parser, cross-page chunker, BM25 search
│   ├── llm.py               # Grounded synthesizer (Deterministic fallback + OpenAI/Gemini)
│   ├── static/
│   │   ├── css/style.css    # Clean, high-contrast, responsive shop-floor styling
│   │   └── js/app.js        # Minimal client logic, speech-to-text, citations
│   └── templates/
│       └── index.html       # Clean entry box & answer UI
├── data/                    # Plant SOPs and manuals (PDFs)
│   ├── MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf
│   ├── QC-SOP-014_Rev03_Incoming_Material_Inspection.pdf
│   ├── QC-SOP-014_Rev04_Incoming_Material_Inspection.pdf
│   ├── SAF-SOP-003_Lockout_Tagout_Procedure.pdf
│   └── Sample_Questions.pdf
├── tests/
│   ├── test_rag.py          # 11 automated test cases for queries & guardrails
│   └── test_api.py          # FastAPI endpoint integration tests
├── Dockerfile               # Production Docker container
├── docker-compose.yml       # One-command compose setup
├── requirements.txt         # Dependencies
├── THINKING.md              # Comprehensive strategic & technical write-up
└── README.md                # Project documentation & answer key
```

