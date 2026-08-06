<div align="center">
  <h1>MNEMOSYNE (Μνημοσύνη)</h1>
  <p><strong>Autonomous Multi-Agent Digital Forensics & Temporal Intelligence Platform</strong></p>
  <p><i>The goddess of memory and mother of the Muses.</i></p>
  
  <!-- Badges placeholder -->
  [![Build Status](https://img.shields.io/github/actions/workflow/status/HarshkumarG007/MNEMOSYNE/test.yml?branch=main)](https://github.com/HarshkumarG007/MNEMOSYNE/actions)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  <br />
</div>

## Project Overview

MNEMOSYNE is a **local-first, autonomous digital forensics and intelligence analysis platform** that reconstructs temporal knowledge graphs from digital artifacts. It employs multiple specialized AI agents to perform cross-reference analysis, anomaly detection, and narrative reconstruction—all while running locally on consumer hardware (e.g., an RTX 4060 laptop with 16GB RAM) with **zero data exfiltration**.

Digital forensics today is deeply fragmented, manual, and tool-heavy. Investigators juggle file carvers, timeline tools, and OSINT platforms. These tools give you raw data, but you lose the *holistic narrative* in the noise. Furthermore, enterprise platforms cost thousands of dollars and require uploading highly sensitive, non-consented personal data (PII) to a third-party cloud. MNEMOSYNE bridges these gaps by combining temporal knowledge graphs with a multi-agent debate architecture.

Unlike chatbots that just answer questions, MNEMOSYNE **discovers what you didn’t know to ask**, surfacing hidden connections and evidence chains that human investigators often miss.

---

## Features

- **Autonomous Ingestion:** Validates, identifies formats, extracts metadata, and virus-scans (via ClamAV) evidence files automatically.
- **Local-First & Privacy-Preserving:** Runs entirely on local consumer hardware. Zero cloud data exfiltration. External enrichment uses differential-privacy noise.
- **Multi-Agent Debate:** Resolves conflicting intelligence via structured debates between specialized agents, mediated by a Judge Agent.
- **Cryptographic Audit Log:** Anchors every piece of ingested evidence and analysis step to a tamper-evident Merkle-tree-chained append-only log.
- **Temporal Querying:** Ask time-bound questions (e.g., "Show me how these relationships changed between March and June") and get a graph-native answer.
- **Dynamic VRAM Management:** Intelligently swaps quantized models into GPU memory based on the active task.

---

## Architecture

The system is built on an event-driven message bus orchestrating an asynchronous swarm of AI agents. The backend is powered by FastAPI, wrapping our LangGraph-based agent workflows, while the frontend provides a real-time temporal visualization using React. 

**Key Differentiators:**
1. **Temporal Knowledge Graphs with Provenance**: Every extracted node and edge is versioned with timestamps, confidence scores, and source-evidence hashes. 
2. **Multi-Agent Debate Architecture**: Existing systems suffer from LLM hallucinations. MNEMOSYNE solves this with a **Debate Mediator**: Uncertain conclusions trigger structured debates between specialized agents, with a **Judge Agent** resolving conflicts using confidence-weighted evidence.
3. **Strictly Local, Privacy-Preserving OSINT**: External enrichment (like WHOIS or Breach lookups) adds differential-privacy noise, uses local caches, and never transmits raw PII in the clear.

---

## Screenshots / UI

*(Placeholders for UI Screenshots)*

- **Live Temporal Graph**
  ![Live Temporal Graph Placeholder](https://via.placeholder.com/800x400?text=Live+Temporal+Graph)
- **Event Timeline**
  ![Event Timeline Placeholder](https://via.placeholder.com/800x400?text=Event+Timeline)
- **Real-time Agent Monitor**
  ![Agent Monitor Placeholder](https://via.placeholder.com/800x400?text=Real-time+Agent+Monitor)

---

## Technology Stack

- **Core & API**: Python 3.11, FastAPI, Uvicorn, Pydantic
- **AI & Orchestration**: LangGraph, Llama.cpp (GGUF Quantization), HuggingFace, Sentence-Transformers
- **Knowledge Graph**: Memgraph (Cypher, Neo4j driver)
- **Storage & Integrity**: SQLite (Async), Cryptography (AES-256-GCM, Merkle Trees), ChromaDB (Vector Store)
- **Frontend**: React, TypeScript, Vite, TailwindCSS (via frontend integration)

---

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (for the Memgraph temporal database)
- Poetry (for Python dependency management)
- Git

### Steps
```bash
git clone https://github.com/HarshkumarG007/MNEMOSYNE.git
cd MNEMOSYNE

# Install backend dependencies
poetry install

# Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## Quick Start

1. **Start Memgraph (Temporal Knowledge Graph)**
```bash
docker run -p 7687:7687 memgraph/memgraph
```

2. **Run the FastAPI backend**
```bash
poetry run uvicorn src.mnemosyne.api.main:app --reload
```

3. **Run the Frontend UI**
```bash
cd frontend
npm run dev
```

4. **Run the Quick Demo**
We have included an E2E demo script that automatically uploads a synthetic Enron email dataset to the ingestion pipeline. In a separate terminal:
```bash
poetry run python -m mnemosyne.demo
```
Then navigate to `http://localhost:5173` to view the analysis live.

---

## Project Structure

```text
MNEMOSYNE/
├── src/mnemosyne/
│   ├── agents/          # Agent logic (Supervisor, Extraction, Judge, etc.)
│   ├── api/             # FastAPI routers, auth, and WebSocket endpoints
│   ├── core/            # Configuration and global dependencies
│   ├── evidence/        # Cryptographic evidence store and deduplication
│   ├── graph/           # Memgraph client and temporal schema mapping
│   ├── ingestion/       # File detection, extraction, and virus scanning
│   ├── memory/          # Vector store integration (ChromaDB)
│   ├── models/          # LLM router, embeddings, and VRAM management
│   └── reporting/       # RAG fallback and final report generation
├── frontend/            # React + TS frontend for data visualization
├── tests/               # Pytest unit and integration tests
├── data/                # Sample datasets for testing (e.g., Enron emails)
└── docs/                # Extended architecture and performance documentation
```

---

## AI Architecture

To fit a genuinely multi-agent workflow into an **8GB VRAM budget**, MNEMOSYNE uses dynamic GPU memory management and `llama.cpp` mmap swapping:
- **Hot Models**: `Phi-3-mini` (Fast NER) and `BGE-M3` (RAG) kept loaded in VRAM (~3.7GB).
- **Warm Models**: `Mistral 7B` (Reasoning/Debate) and `Llama 3.1 8B` (General Analysis) loaded on-demand.
- **Cold Models**: `Whisper.cpp` (Audio) and `YOLOv8n` (Computer Vision) loaded per-task.

### The Agent Swarm
- **Ingestion Agent**: Validates and extracts file metadata.
- **Extraction Agent**: Fast NER and relationship extraction.
- **Temporal Analyst**: Constructs timelines via Allen's interval algebra.
- **Correlation Agent**: Cross-references entities via similarity learning.
- **OSINT Agent**: Privacy-preserving external enrichment.
- **Anomaly Detector**: Flags timeline outliers.
- **Judge Agent**: Mediates debates and applies Bayesian confidence updating.

---

## Knowledge Graph

Traditional knowledge graph projects don't attempt evidentiary integrity, and they lack a temporal dimension (time), treating relationships as static facts rather than evolving realities.

MNEMOSYNE utilizes **Memgraph**, an in-memory graph database, to store relationships with **valid_from** and **valid_to** properties. This allows investigators to run Cypher queries that step forwards or backwards in time, effectively enabling a DVR-like playback of criminal networks and event timelines.

---

## Security

MNEMOSYNE operates strictly on artifacts the user already possesses and is authorized to analyze. 
- **Encryption**: A local SQLite blob store uses **SHA-256 content-addressed deduplication** and AES-256-GCM encryption.
- **Audit Trails**: Every analysis step is chained to a **Merkle-tree**, creating a tamper-evident audit trail without any external blockchain dependencies.
- **Data Privacy**: No data is uploaded to third-party APIs. All LLM inference is performed locally.

---

## Performance

- **FastNER**: Uses quantized Phi-3 for rapid entity extraction.
- **Async Processing**: Implements python `asyncio` across all I/O bound tasks (database querying, file reading).
- For a deeper dive into performance metrics and benchmarks, see the [Performance Optimization Report](docs/performance.md).

---

## Roadmap

- [ ] Implement audio transcription via Whisper.cpp
- [ ] Add Computer Vision extraction via YOLOv8n
- [ ] Expand OSINT integrations (e.g., Shodan, HaveIBeenPwned)
- [ ] Build standalone desktop electron application
- [ ] Implement fully-automated forensic report exports in PDF/Docx

---

## Contributing

We welcome contributions! Please review our standard GitHub flow:
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

*MNEMOSYNE is a tool for defensive security, authorized forensics, and intelligence analysis.*

---

## Acknowledgements

- [LangGraph](https://github.com/langchain-ai/langgraph) for the agent orchestration framework.
- [Llama.cpp](https://github.com/ggerganov/llama.cpp) for making local quantized LLM inference possible.
- [Memgraph](https://memgraph.com/) for the blazing-fast temporal graph database.
- The open-source digital forensics community.
