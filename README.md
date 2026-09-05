# AURA // Finance Controller

### Autonomous Unified Reconciliation & Exception Resolution

**AURA Finance Controller** is an AI-assisted financial reconciliation platform designed to automate the reconciliation of transactional data across heterogeneous financial sources such as ERP records, bank statements, payment gateways, and internal ledgers.

AURA combines **deterministic financial computation** with **AI-powered anomaly investigation**. Financial matching and numerical calculations remain rule-based and reproducible, while AI is isolated to the investigation layer where it analyzes exceptions, identifies potential root causes, and generates bounded recommendations.

> **Core principle:** AI investigates financial exceptions. It does not control the financial mathematics.

---

## Overview

Traditional financial reconciliation often depends on manually comparing records across multiple systems, identifying mismatches, investigating exceptions, and preparing reports.

This approach becomes expensive and error-prone as transaction volume increases.

AURA addresses this workflow through an automated pipeline:

```text
Financial Data Sources
        │
        ▼
┌─────────────────────┐
│ Data Ingestion      │
│ & Normalization     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Deterministic       │
│ Reconciliation      │
└──────────┬──────────┘
           │
      ┌────┴─────┐
      │          │
   Matched    Exceptions
      │          │
      │          ▼
      │    ┌───────────────┐
      │    │ AI            │
      │    │ Investigation │
      │    └───────┬───────┘
      │            │
      │            ▼
      │    Root Cause / Risk
      │    / Recommendation
      │
      └──────────┬───────────
                 ▼
        Audit & Reporting
```

The result is a reconciliation workflow that prioritizes **accuracy, traceability, explainability, and graceful failure handling**.

---

## Key Features

### 1. Deterministic Reconciliation

AURA performs the core reconciliation process using deterministic rules rather than asking an LLM to decide whether financial records match.

This provides:

* Reproducible results
* Predictable matching logic
* Exact numerical calculations
* Clear reconciliation states
* Reduced risk of AI-generated financial errors

The AI layer is intentionally kept outside the core financial computation path.

---

### 2. AI-Powered Exception Investigation

Records that cannot be reconciled automatically are routed to an AI investigation layer.

The investigator can analyze anomalies such as:

* Missing transactions
* Unexpected gateway fees
* Amount discrepancies
* Duplicate or incomplete records
* Potential causes of reconciliation failures

The AI output is used as **investigative intelligence**, rather than as an authoritative financial calculation.

---

### 3. Real-Time 3D Ledger Map

AURA includes an interactive WebGL-based visualization that represents financial records spatially.

The visualization provides a command-center style view of:

* Transaction relationships
* Reconciliation states
* Exception locations
* Risk levels
* Backend record activity

The 3D layer is state-driven and connected to the application's live data model.

**Technology:** React Three Fiber + Three.js

---

### 4. Chaos Monkey Protocol

AURA includes a built-in infrastructure stress-testing mode.

The Chaos Monkey protocol intentionally introduces simulated failure conditions to test whether the system can:

1. Detect the failure
2. Avoid crashing the user experience
3. Enter a controlled fallback state
4. Preserve existing reconciliation information
5. Communicate degraded system state

This makes failure handling part of the product rather than an afterthought.

---

### 5. Audit Export

Reconciliation results can be exported into CSV format for downstream analysis.

The exported audit information can include:

* Transaction metrics
* Reconciliation status
* Exception information
* AI investigation results
* Risk assessments
* Supporting reasoning

This makes AURA suitable for further analysis in spreadsheet, BI, or data-processing workflows.

---

## Architecture

AURA follows a separation-of-concerns architecture with three primary layers.

### Frontend

```text
React
  │
  ├── Dashboard / Command Center
  ├── Reconciliation Controls
  ├── Transaction Visualization
  ├── Exception Monitoring
  └── 3D Ledger Map
```

Built with:

* React
* Vite
* Tailwind CSS
* Framer Motion
* Lucide React
* Three.js
* React Three Fiber
* React Three Drei
* Axios

---

### Backend

```text
FastAPI
   │
   ├── Data Ingestion
   ├── Data Normalization
   ├── Reconciliation Engine
   ├── Exception Detection
   ├── AI Investigation
   └── Audit Export
        │
        ▼
     Pandas
```

The backend is responsible for deterministic data processing and API orchestration.

**Core technologies:**

* Python
* FastAPI
* Pandas
* Uvicorn

---

### AI Investigation Layer

```text
Exception
    │
    ▼
Investigation Context
    │
    ▼
Qwen / Groq API
    │
    ├── Root Cause Analysis
    ├── Missing Record Detection
    ├── Fee Analysis
    └── Bounded Recommendations
```

AI is deliberately isolated from the reconciliation engine.

This architectural boundary is important because an LLM should not be responsible for determining whether:

```text
₹10,000 = ₹10,000
```

That belongs to deterministic software.

The model is better suited to answering:

> "Why does this transaction appear to differ from the expected settlement?"

---

## Reconciliation Philosophy

AURA is built around a simple architectural rule:

### Deterministic where correctness matters.

### Probabilistic where investigation matters.

| Responsibility            | Approach      |
| ------------------------- | ------------- |
| Amount calculations       | Deterministic |
| Record matching           | Rule-based    |
| Transaction normalization | Deterministic |
| Reconciliation status     | Rule-based    |
| Exception detection       | Deterministic |
| Root-cause investigation  | AI-assisted   |
| Anomaly explanation       | AI-assisted   |
| Risk interpretation       | AI-assisted   |
| Audit export              | Deterministic |

This separation reduces the blast radius of AI-generated errors while still using AI where it provides the most value.

---

## Technology Stack

| Layer                | Technology        |
| -------------------- | ----------------- |
| Frontend             | React             |
| Build Tool           | Vite              |
| Styling              | Tailwind CSS      |
| Animation            | Framer Motion     |
| Icons                | Lucide React      |
| 3D Visualization     | Three.js          |
| 3D React Integration | React Three Fiber |
| HTTP Client          | Axios             |
| Backend              | FastAPI           |
| Data Processing      | Pandas            |
| Server               | Uvicorn           |
| AI Investigation     | Qwen / Groq API   |
| Containerization     | Docker            |
| Orchestration        | Docker Compose    |
| Data Export          | CSV               |

---

## Project Structure

```text
AURA-Financial-Controller/
│
├── backend/
│   ├── app/
│   │   ├── ...
│   │   └── main.py
│   ├── data/
│   ├── Dockerfile
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── ...
│   │   └── components/
│   ├── package.json
│   ├── vite.config.*
│   └── ...
│
├── data/
│   └── synthetic/
│
├── screenshots/
│
├── Screen Recodings/
│
├── docker-compose.yml
├── .dockerignore
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

Install the following before running AURA locally:

* Python 3.10+
* Node.js 18+
* npm
* Git

For containerized execution:

* Docker
* Docker Compose

---

## Option 1 — Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Piyushsingh0216/AURA-Financial-Controller.git

cd AURA-Financial-Controller
```

### 2. Start the backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload
```

The backend will run on:

```text
http://localhost:8000
```

---

### 3. Start the frontend

Open another terminal:

```bash
cd frontend

npm install

npm run dev
```

The Vite development server will provide the frontend URL in the terminal, typically:

```text
http://localhost:5173
```

---

## Option 2 — Docker Compose

AURA also includes a Docker Compose configuration for running the frontend and backend together. The current Compose setup exposes the backend on port `8000` and the frontend container on port `3000`.

From the repository root:

```bash
docker compose up --build
```

Then access the application through the frontend container.

To stop the services:

```bash
docker compose down
```

---

## Environment Configuration

Create the appropriate environment configuration for the backend before enabling AI-powered investigation.

Example:

```env
# AI Provider
GROQ_API_KEY=your_api_key

# Application
ENVIRONMENT=development

# Optional configuration
LOG_LEVEL=INFO
```

**Never commit API keys, credentials, or production secrets to Git.**

Use environment variables or a local `.env` file that is excluded from version control.

---

## Using AURA

Once the application is running:

### Step 1 — Open the Command Center

Launch the frontend in your browser.

### Step 2 — Execute Reconciliation

Trigger the reconciliation workflow to ingest the available financial dataset.

### Step 3 — Review Results

AURA separates records into:

* Successfully reconciled records
* Exceptions requiring investigation

### Step 4 — Investigate Exceptions

Exceptions are passed to the AI investigation layer for additional analysis.

The system can provide:

* Suspected root causes
* Fee discrepancies
* Missing-record analysis
* Risk assessment
* Recommended next actions

### Step 5 — Export the Audit

Generate a CSV report containing reconciliation and investigation information for downstream analysis.

---

## Failure Handling

Financial systems should not assume that every dependency will remain available.

AURA therefore includes explicit failure simulation through the **Chaos Monkey Protocol**.

Conceptually:

```text
Normal Operation
      │
      ▼
Infrastructure Failure
      │
      ▼
Failure Detection
      │
      ▼
Graceful Degradation
      │
      ▼
System Remains Observable
```

The purpose is not simply to demonstrate that the application can survive an artificial failure.

It tests whether the architecture has a defined answer to:

> "What happens when one of the things this system depends on stops working?"

---

## Security & Reliability Principles

AURA follows several principles intended for financial-data workflows:

### AI Isolation

The LLM is not the source of truth for financial calculations.

### Deterministic Processing

Critical reconciliation operations are performed through deterministic application logic.

### Explicit Exception Handling

Failed matches are surfaced as exceptions rather than silently accepted.

### Environment-Based Secrets

API credentials should be supplied through environment configuration rather than source code.

### Auditable Outputs

Reconciliation and investigation results can be exported for downstream review.

---

## Current Limitations

AURA is an engineering prototype demonstrating an AI-assisted reconciliation architecture.

It should **not** currently be treated as a fully certified financial production system.

Before production deployment, additional work would be required around areas such as:

* Authentication and authorization
* Role-based access control
* Encryption and key management
* Production database architecture
* Immutable audit logging
* Data retention policies
* Observability and alerting
* Comprehensive automated testing
* Regulatory and compliance requirements
* High-availability deployment
* Production-grade secret management
* Formal validation of AI-generated recommendations

These limitations are intentional boundaries of the current project rather than claims that the prototype already satisfies financial-industry production requirements.

---

## Why AURA?

The interesting part of AURA is not simply "using AI for finance."

The architectural problem is more specific:

> **How can AI be introduced into a financial workflow without allowing probabilistic model output to become the source of truth for deterministic financial operations?**

AURA addresses this by separating:

```text
                    AURA
                      │
          ┌───────────┴───────────┐
          │                       │
   COMPUTATION               INVESTIGATION
          │                       │
   Deterministic                 AI
          │                       │
   Exact matching          Root-cause analysis
   Exact calculations     Anomaly explanation
   Reconciliation         Recommendations
          │                       │
          └───────────┬───────────┘
                      │
                Auditable Result
```

This architecture allows AI to add intelligence without giving an LLM authority over the financial ledger itself.

---

## Deployment

A deployed version of the application is available at:

**[AURA Finance Controller](https://aura-financial-controller.vercel.app/)**

The repository is available on GitHub:

**[Piyushsingh0216/AURA-Financial-Controller](https://github.com/Piyushsingh0216/AURA-Financial-Controller)**

---

## Screenshots & Demonstration

The repository contains dedicated directories for:

* Application screenshots
* Screen recordings
* Synthetic financial datasets

These assets can be used to understand the application's interface and workflow without requiring a full local setup.

---

## Future Roadmap

Potential next-stage improvements include:

* [ ] PostgreSQL-backed production persistence
* [ ] User authentication and RBAC
* [ ] Multi-tenant financial workspaces
* [ ] ERP connector framework
* [ ] Bank statement ingestion
* [ ] Payment gateway integrations
* [ ] Advanced reconciliation rule configuration
* [ ] Human-in-the-loop exception approval
* [ ] Immutable audit trails
* [ ] Automated reconciliation scheduling
* [ ] Real-time monitoring and alerts
* [ ] Comprehensive unit and integration test coverage
* [ ] Production observability
* [ ] Containerized production deployment
* [ ] Model evaluation and AI response guardrails

---

## License

This project is currently maintained as a personal engineering project.

License information will be added when the project is formally released under an open-source license.

---

## Author

### Piyush Singh

**Software Engineering | AI/ML | Data | Cloud**

GitHub:
[github.com/Piyushsingh0216](https://github.com/Piyushsingh0216)

---

<p align="center">
  <strong>AURA // Finance Controller</strong><br>
  Deterministic reconciliation. Intelligent investigation. Auditable decisions.
</p>
