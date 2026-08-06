<div align="center">
  <h1>MNEMOSYNE (Μνημοσύνη)</h1>
  <p><strong>Autonomous Multi-Agent Digital Forensics & Temporal Intelligence Platform</strong></p>
  <p><i>The goddess of memory and mother of the Muses.</i></p>
  
  <br />
</div>

MNEMOSYNE is a **local-first, autonomous digital forensics and intelligence analysis platform** that reconstructs temporal knowledge graphs from digital artifacts. It employs multiple specialized AI agents to perform cross-reference analysis, anomaly detection, and narrative reconstruction—all while running locally on consumer hardware (e.g., an RTX 4060 laptop with 16GB RAM) with **zero data exfiltration**.

---

## 🛑 The Problem: What Current Systems Lack

Digital forensics today is deeply fragmented, manual, and tool-heavy:
1. **The Disconnected Narrative:** Investigators juggle file carvers, timeline tools (like Autopsy or Plaso), and OSINT platforms. These tools give you raw data, but you lose the *holistic narrative* in the noise.
2. **The eDiscovery Cloud Trap:** Enterprise platforms cost thousands of dollars and require uploading highly sensitive, non-consented personal data (PII) to a third-party cloud.
3. **The Static Graph Flaw:** Traditional knowledge graph projects don't attempt evidentiary integrity, and they lack a temporal dimension (time), treating relationships as static facts rather than evolving realities.

## 🌉 The Solution: How MNEMOSYNE Dominates the Space

MNEMOSYNE bridges these gaps by combining three hard problems rarely tackled together:

1. **Temporal Knowledge Graphs with Provenance**: Every extracted node and edge is versioned with timestamps, confidence scores, and source-evidence hashes. You can ask *"Show me how this person's relationships changed between March and June"* and get a graph-native answer backed by cryptographic chain-of-custody.
2. **Multi-Agent Debate Architecture**: Existing systems suffer from LLM hallucinations. MNEMOSYNE solves this with a **Debate Mediator**: Uncertain conclusions trigger structured debates between specialized agents (e.g., *Entity Extractor* vs. *Temporal Analyst*), with a **Judge Agent** resolving conflicts using confidence-weighted evidence.
3. **Strictly Local, Privacy-Preserving OSINT**: External enrichment (like WHOIS or Breach lookups) adds differential-privacy noise, uses local caches, and never transmits raw PII in the clear. 

Unlike chatbots that just answer questions, MNEMOSYNE **discovers what you didn’t know to ask**, surfacing hidden connections and evidence chains that human investigators often miss.

---

## 🧠 System Architecture & Innovation

### The Multi-Agent Pool
MNEMOSYNE uses an AsyncIO message bus and LangGraph to orchestrate specialized AI agents:
* **Ingestion Agent**: Validates, identifies formats, extracts metadata, and virus-scans (ClamAV).
* **Extraction Agent**: Fast NER and relationship extraction using **Phi-3 (3.8B)**.
* **Temporal Analyst**: Constructs timelines and parses temporal constraints via Allen's interval algebra.
* **Correlation Agent**: Cross-references entities across documents via similarity learning.
* **OSINT Agent**: Privacy-preserving external enrichment with strict differential-privacy budgets.
* **Anomaly Detector**: Flags timeline outliers and unusual access patterns.
* **Integrity Agent**: Maintains the cryptographic Merkle-tree audit log of all evidence.
* **Judge Agent**: Uses **Mistral 7B Instruct** to mediate debates and apply Bayesian confidence updating.

### Quantized Model Ensemble (VRAM Optimization)
To fit a genuinely multi-agent workflow into an **8GB VRAM budget**, MNEMOSYNE uses dynamic GPU memory management and `llama.cpp` mmap swapping:
- **Hot Models**: `Phi-3` (Fast NER) and `BGE-M3` (RAG) kept loaded in VRAM (~3.7GB).
- **Warm Models**: `Mistral 7B` (Reasoning) and `Llama 3.1 8B` (General Analysis) loaded on-demand.
- **Cold Models**: `Whisper.cpp` (Audio) and `YOLOv8n` (Computer Vision) loaded per-task.

### Evidence Store & Cryptographic Audit
A local SQLite blob store uses **SHA-256 content-addressed deduplication** and AES-256-GCM encryption. Every analysis step and piece of ingested evidence is anchored to a **Merkle-tree-chained, append-only log**—a tamper-evident audit trail with no external blockchain dependency.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (for the Memgraph temporal database)
- Poetry (for Python dependency management)

### 1. Backend Setup
```bash
git clone https://github.com/HarshkumarG007/MNEMOSYNE.git
cd MNEMOSYNE

# Install dependencies
poetry install

# Start Memgraph (Temporal Knowledge Graph)
docker run -p 7687:7687 memgraph/memgraph

# Run the FastAPI backend
poetry run uvicorn src.mnemosyne.api.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Quick Demo
Run the included E2E demo script, which will boot the server and automatically upload a synthetic Enron email dataset to the Ingestion pipeline:
```bash
poetry run python -m mnemosyne.demo
```
Then navigate to `http://localhost:5173` to view the Live Temporal Graph, the Event Timeline, and the Real-time Agent Monitor!

---

## 📚 Documentation & Deep Dives
For full insights into the architecture and API:
- [Performance Optimization Report](docs/performance.md)
- [API Specification (OpenAPI)](docs/api/openapi.json)
- [Detailed Architecture Spec](docs/architecture/) (Coming Soon)

## 🛡️ License
MIT License.

*MNEMOSYNE operates strictly on artifacts the user already possesses and is authorized to analyze. It is a tool for defensive security, authorized forensics, and intelligence analysis.*
