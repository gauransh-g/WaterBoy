# 💧 WaterBoy: Groundwater AI & Decadal Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue.svg)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38bdf8.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**WaterBoy** is an evidence-backed groundwater intelligence platform designed to empower citizens, researchers, and policymakers across India with verifiable, data-grounded insights into groundwater reserves, extraction dynamics, conservation methodologies, **all 38 States and Union Territories**, and **decadal historical trends (2015–2025)**.

The system combines official Dynamic Groundwater Resource Assessment reports from the **Central Ground Water Board (CGWB)**, Ministry of Jal Shakti, with a sub-25ms semantic retrieval engine (SentenceTransformers + Vectorized Inner-Product Cosine Similarity) and a modern, accessible web dashboard.

---

## 📑 Table of Contents
- [1. System Architecture](#1-system-architecture)
- [2. Comprehensive Multi-Year & Decadal Intelligence](#2-comprehensive-multi-year--decadal-intelligence)
- [3. Key Capabilities](#3-key-capabilities)
- [4. Project Structure](#4-project-structure)
- [5. Installation & Quick Start](#5-installation--quick-start)
- [6. API Reference](#6-api-reference)
- [7. Limitations & Future Roadmap](#7-limitations--future-roadmap)
- [8. License & Attribution](#8-license--attribution)

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 React + TypeScript Frontend                 │
│  - Clean Light Theme (Crisp White & Sky Blue Accents)       │
│  - Conversational Evidence-Backed AI Chat                   │
│  - Multi-Year Historical Trend Visualizer (2021–2025)       │
│  - All 38 States & UTs Dynamic Assessment Explorer          │
│  - Verifiable Evidence Excerpt & Source Inspector Modal     │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / REST APIs
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend (Uvicorn)                │
│  - CORS Middleware & Input Validation (Pydantic v2)         │
│  - /api/chat • /api/search • /api/groundwater • /api/health │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
┌──────────────▼─────────────┐ ┌──────────────▼───────────────┐
│     Hybrid RAG Pipeline    │ │     CGWB Tabular Database    │
│ - SentenceTransformers     │ │ - SQLite In-Memory / Disk    │
│   (all-MiniLM-L6-v2)       │ │ - 3,093 Assessment Units     │
│ - 1,664 Vector Chunks      │ │ - All 38 States & UTs        │
│ - Adaptive Domain Detection│ │ - Multi-Year Assessments     │
│   (No False Refusals)      │ │   (2021-22, 22-23, 23-24,    │
│ - Evidence Grounding       │ │    2024-25 & Decadal 2015-25)│
└────────────────────────────┘ └──────────────────────────────┘
```

---

## 2. Comprehensive Multi-Year & Decadal Intelligence

Unlike isolated snapshot tools, WaterBoy unifies multi-year CGWB assessment cycles across consecutive cycles (**2021–2022, 2022–2023, 2023–2024, and 2024–2025**) along with **10-year decadal trends (2015 to 2025)**:

- **Nationwide Coverage (All 38 States & UTs)**: Ingests 3,093 dynamic assessment records spanning every state and union territory in India (from Punjab, Rajasthan, and Uttar Pradesh to Kerala, Lakshadweep, and Ladakh).
- **Decadal Trajectories (2015–2025)**: Ingests 10-year macro-trends tracking national groundwater recharge growth (432 BCM in 2017 to 451 BCM in 2025), extraction trends, and block recovery.
- **Adaptive Query Intelligence**: Automatically extracts geographic mentions and maps natural language questions to state trajectories without false refusal cutoffs.
- **Interactive Multi-Year Visualizations**: Visualizes Stage of Extraction (%) and recharge volumes over time with dynamic filtering by cycle and state.

---

## 3. Key Capabilities

1. **Grounded Question Answering with Citations**:
   - Every answer cites exact source documents with inline references `[1]`, `[2]`.
   - Clicking any citation opens an evidence modal displaying chunk ID, section, relevance score, assessment cycle, and verifiable source text.
2. **Intelligent Domain Guard (Anti-Hallucination without False Refusals)**:
   - In-domain inquiries relating to Indian hydrology, states, water tables, agriculture, and government schemes are dynamically recognized and answered.
   - Out-of-scope non-hydrological queries (e.g. stock prices, sports, general pop trivia) are safely refused without fabricating answers.
3. **Official Central Ground Water Board (CGWB) Dynamic Assessment**:
   - Covers 3,093 assessment units across all 38 states and UTs.
   - Computes Stage of Ground Water Extraction (SOE) and categorizes units into **Safe**, **Semi-Critical**, **Critical**, and **Over-Exploited**.
4. **Sub-25ms Retrieval Latency**:
   - L2-normalized vector dot product computation enables instantaneous responses even on standard CPU workstations.
5. **Clean, Modern UI Experience**:
   - Built with a clean white aesthetic accented with sky blue typography, responsive cards, and dynamic data filtering.

---

## 4. Project Structure

```
WaterBoy (SIH Project)/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI router endpoints (chat, data, eval)
│   │   ├── data/                # CGWB multi-year loader & SQLite database
│   │   ├── evaluation/          # Internal benchmark suite & test cases
│   │   ├── models/              # Pydantic request/response schemas
│   │   ├── rag/                 # Chunker, Embeddings, Vector Store, Generator
│   │   ├── config.py            # Global settings & environment vars
│   │   └── main.py              # FastAPI app & lifespan handlers
│   ├── data_store/              # Persistent vector index & benchmark output
│   ├── knowledge_base/          # Curated CGWB & policy markdown documents (10 guides)
│   ├── tests/                   # Pytest unit & integration test suite
│   ├── ingest_data.py           # Offline multi-year knowledge ingestion script
│   ├── run_server.py            # Uvicorn startup entrypoint
│   └── verify_endpoints.py      # Automated benchmark verification script
├── frontend/
│   ├── src/
│   │   ├── components/          # Navbar, ChatInterface, GroundwaterDashboard, etc.
│   │   ├── services/            # REST API client
│   │   ├── types/               # TypeScript interfaces
│   │   ├── App.tsx              # Main dashboard view switcher
│   │   └── main.tsx             # React entrypoint
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── start_waterboy.bat           # One-click Windows startup script
├── README.md
└── LICENSE
```

---

## 5. Installation & Quick Start

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# Clone the repository
git clone <repo-url>
cd "WaterBoy (SIH Project)"

# Install Python dependencies
pip install -r backend/requirements.txt

# Ingest All 38 States & UTs Multi-Year CGWB Datasets (Builds Vector Index)
python backend/ingest_data.py

# Start Backend Server
python backend/run_server.py
```
Backend API will be running on **http://127.0.0.1:8000** (Interactive OpenAPI docs: **http://127.0.0.1:8000/docs**).

### 2. Frontend Setup
```bash
# In a new terminal:
cd frontend

# Install Node dependencies
npm install

# Start Vite Development Server
npm run dev
```
Frontend UI will be running on **http://127.0.0.1:5173**.

### 3. One-Click Windows Launch
Double-click `start_waterboy.bat` to launch both backend and frontend servers simultaneously in separate terminal windows.

---

## 6. API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health, 1,664 indexed chunks, and database stats |
| `POST` | `/api/chat` | Evidence-backed RAG question answering across decadal & multi-year cycles |
| `POST` | `/api/search` | Direct hybrid semantic & lexical chunk search |
| `GET` | `/api/groundwater/summary` | National overview (Safe vs Over-Exploited units, optional `year` param) |
| `GET` | `/api/groundwater/states` | State-by-state assessment metrics across all 38 states/UTs |
| `GET` | `/api/groundwater/trends` | Historical multi-year progression for any given state (2021–2025) |
| `GET` | `/api/groundwater/district/{state}/{district}` | District-level assessment unit breakdown |
| `POST` | `/api/evaluate` | Internal evaluation benchmark endpoint |

---

## 7. Limitations & Future Roadmap
- **High-Resolution Karst & Urban Sub-blocks**: Future updates can include ward-level telemetry data where municipal authorities publish them.
- **Geospatial Mapping**: Direct GeoJSON district polygon layers for MapLibre integration.
- **Satellite Remote Sensing Integration**: Expansion with Google Earth Engine for Drought Severity Index (VCI / NDVI) and evapotranspiration modeling.

---

## 8. License & Attribution
- Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
- Assessment data, terminology, and hydrogeological equations sourced from official publications by the **Central Ground Water Board (CGWB)**, Department of Water Resources, River Development & Ganga Rejuvenation, Ministry of Jal Shakti, Government of India.
