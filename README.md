# MNEMOSYNE

**Autonomous Multi-Agent Digital Forensics & Temporal Intelligence Platform**

MNEMOSYNE is a local-first, autonomous digital forensics and intelligence analysis platform that reconstructs temporal knowledge graphs from digital artifacts. It enables investigators, researchers, and privacy-conscious users to understand the complete narrative hidden within their data without exfiltrating it to the cloud.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js (for frontend)
- Docker (for database services)

### Setup

1. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

2. Install pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

3. Run tests to verify setup:
   ```bash
   poetry run pytest
   ```

## License
MIT License
