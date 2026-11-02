# 🏛️ WaterBoy System Architecture & Technical Specifications

This document outlines the architecture, data schemas, retrieval mechanics, and system design principles of the **WaterBoy Groundwater AI & Multi-Year Intelligence Platform**.

---

## 1. High-Level Architecture Overview

WaterBoy follows a modular decoupled client-server architecture designed for sub-25ms evidence retrieval, transparent citation attribution, and interactive multi-year groundwater exploration:

```
┌──────────────────────────────────────────────────────────────┐
│                  React + TypeScript Client                   │
│   - Clean White Theme (Sky Blue Font & Accent Palette)       │
│   - Conversational AI Assistant with Citation Modals         │
│   - Multi-Year Historical Trend Visualizer (Area/Line)       │
│   - Dynamic State & District Assessment Explorer (All 38)    │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP / REST (Vite Reverse Proxy)
┌──────────────────────────────▼───────────────────────────────┐
│                    FastAPI Backend (Uvicorn)                 │
│   - Pydantic v2 Request/Response Validation                  │
│   - CORS Middleware & Adaptive Query Routing                 │
│   - /api/chat • /api/search • /api/groundwater • /api/health │
└──────────────┬───────────────────────────────┬───────────────┘
               │                               │
┌──────────────▼──────────────┐ ┌──────────────▼───────────────┐
│     Hybrid RAG Pipeline     │ │    Structured CGWB Database   │
│ - SentenceTransformers      │ │ - SQLite In-Memory / Disk    │
│   (all-MiniLM-L6-v2)        │ │ - 3,093 Multi-Year Units     │
│ - 1,664 Embedded Chunks     │ │ - 4 Assessment Cycles        │
│ - Dot-Product Cosine Sim    │ │   (2021-22, 22-23, 23-24,    │
│ - Adaptive Domain Detection │ │    2024-25 & Decadal 2015-25)│
│ - Anti-Hallucination Guard  │ │ - Fast Aggregation & Trends  │
└─────────────────────────────┘ └──────────────────────────────┘
```

---

## 2. Structured Groundwater Database (SQLite)

Located at `backend/data_store/groundwater.db`, the structured database indexes **3,093 authentic assessment units** across all 38 States and Union Territories of India.

### Table Schema: `assessment_units`

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER PRIMARY KEY` | Auto-incrementing unit ID |
| `state` | `TEXT NOT NULL` | State or Union Territory name |
| `district` | `TEXT NOT NULL` | District or administrative block identifier |
| `location_name` | `TEXT NOT NULL` | Specific assessment unit locality name |
| `category` | `TEXT NOT NULL` | CGWB status: `Safe`, `Semi Critical`, `Critical`, `Over Exploited`, `Salinity` |
| `stage_of_extraction` | `REAL` | Extraction as % of annual extractable resource ($\text{SOE}$) |
| `total_recharge_ham` | `REAL` | Annual groundwater replenishment in Hectare-Meters (ham) |
| `total_extraction_ham`| `REAL` | Annual draft (irrigation + domestic + industrial) in ham |
| `availability_for_future_use_ham` | `REAL` | Surplus availability for developmental allocation |
| `rainfall_mm` | `REAL` | Normal monsoon precipitation in millimeters |
| `geology` | `TEXT` | Hydrogeological formation (Alluvium, Deccan Basalt, Crystalline Hard Rock) |
| `water_table_trend` | `TEXT` | Static water level trajectory (Rising, Falling, Stable) |
| `assessment_year` | `TEXT NOT NULL` | Assessment cycle (`2021-2022`, `2022-2023`, `2023-2024`, `2024-2025`) |

---

## 3. Knowledge Base & Vector Index

### Reference Documents (`backend/knowledge_base/documents/`)
1. `01_cgwb_resource_estimation_methodology.md`: Official GEC-2015 formulas, rainfall infiltration factors, and water balance equations.
2. `02_atal_bhujal_yojana_guidelines.md`: ATAL JAL guidelines, 80 priority districts, and community Water Security Plans.
3. `03_artificial_recharge_and_rainwater_harvesting.md`: CGWB Master Plan recharge structures (percolation tanks, check dams, subsurface dykes).
4. `04_groundwater_quality_and_contamination_standards.md`: BIS IS 10500:2012 permissible limits (Fluoride, Arsenic, Nitrate, Heavy Metals).
5. `05_ingres_portal_and_digital_groundwater_monitoring.md`: Centralized INGRES architecture, GIS layers, and DWLR sensor telemetry.
6. `06_decadal_groundwater_trends_india_2015_2025.md`: 10-year macro-trends, national replenishment growth (432 to 451 BCM), and block recovery.
7. `07_all_states_and_uts_hydrogeology_profiles.md`: Hydrogeological characteristics, aquifer types, and status for all 38 states/UTs.
8. `08_aquifer_systems_depth_to_water_and_fluctuations.md`: 14 Principal Aquifer Systems and seasonal water table fluctuations.
9. `09_national_groundwater_policies_and_flagship_schemes.md`: CGWA NOC extraction regulations, JJM, NAQUIM 1.0 & 2.0.
10. `10_water_wells_pumping_machinery_and_dwlr_telemetry.md`: Well hydraulics, dug wells, deep borewells, and solar irrigation pumps.

### Vector Storage (`backend/data_store/vector_index/`)
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors).
- **Index Architecture**: L2-normalized inner-product cosine similarity matrix with fallback to vectorized NumPy dot products, ensuring zero DLL runtime dependencies across operating systems.
- **Total Indexed Items**: 1,664 chunks spanning reference guidelines, state-level multi-year trajectories, and prominent district assessment units.

---

## 4. Adaptive Retrieval & Anti-Hallucination Safeguards

```
User Query
    │
    ▼
[Extract Location Hints] ──► (Detected State: e.g. "Delhi", "Punjab")
    │
    ▼
[Domain Check] ────────────► Matches 70+ hydrogeology / water / geography keywords?
    │                                │
    ├───────────── YES ──────────────┤
    │                                │
    ▼                                ▼
[Adaptive Retrieval]       [Out-of-Domain Guard]
- Top-k = 4 Chunks         - Similarity < 0.28 AND No domain words
- Fallback to Global if    - Safely refuse without hallucinating
  state filter < 2 chunks
    │
    ▼
[Grounded Answer Synthesizer]
- Extracts factual sentences
- Injects verifiable citation badges [1], [2]
- Sub-25ms response latency
```

---

## 5. Frontend Design Principles
- **Aesthetic**: Crisp white canvas (`bg-white`, `bg-slate-50`) paired with sky blue typography (`text-sky-600`, `text-sky-700`) and border accents.
- **Accessibility**: Clear visual indicators for groundwater stress (Safe = Sky Blue, Semi-Critical = Amber, Critical = Orange, Over-Exploited = Rose).
- **Transparency**: Every claim in the assistant links directly to an evidence drawer detailing relevance percentage, source document, chunk ID, and exact source text.
