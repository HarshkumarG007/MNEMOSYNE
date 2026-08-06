# MNEMOSYNE

MNEMOSYNE is a Multi-Agent Digital Forensics Platform designed to run locally on consumer hardware (e.g., RTX 4060 laptop, 16GB RAM). It uses specialized LLM agents to ingest, extract, and correlate evidence, visualizing it in a dynamic knowledge graph.

## Architecture

![Architecture](docs/architecture/flow.png)

### Core Components
- **FastAPI Backend**: Orchestrates the LLM agents and exposes REST/WebSocket endpoints.
- **LangGraph Agents**: A pool of agents (`IngestionAgent`, `ExtractionAgent`, `TemporalAgent`, `CorrelationAgent`, `JudgeAgent`) orchestrated by a `SupervisorAgent`.
- **Memgraph Database**: Stores extracted entities (Persons, Files, Events) and their temporal relationships.
- **Evidence Store**: A content-addressed, deduplicated, and optionally encrypted local SQLite blob store.
- **React Frontend**: A Vite-powered dashboard featuring Cytoscape.js for graph visualization and live WebSocket streams for monitoring agent activity.

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (for Memgraph)
- Poetry (for Python dependency management)

### 1. Backend Setup
```bash
git clone https://github.com/HarshkumarG007/MNEMOSYNE.git
cd MNEMOSYNE

# Install dependencies
poetry install

# Start Memgraph
docker run -p 7687:7687 memgraph/memgraph

# Run the backend
poetry run uvicorn src.mnemosyne.api.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Quick Demo
Run the included E2E demo script, which will start the server and upload a sample Enron email dataset:
```bash
poetry run python -m mnemosyne.demo
```
Then navigate to `http://localhost:5173` to view the Live Graph and Agent Monitor!

## Documentation
- [API Spec (OpenAPI)](docs/api/openapi.json)
- [Architecture Details](docs/architecture/README.md)

## License
MIT
