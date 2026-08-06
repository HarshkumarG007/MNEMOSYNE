import json
import logging
from typing import Any, Dict

from jinja2 import BaseLoader, Environment

logger = logging.getLogger(__name__)

# Basic Markdown Template for the Forensic Report
REPORT_TEMPLATE = """# MNEMOSYNE Forensic Report
**Generated:** {{ timestamp }}

## Executive Summary
{{ summary }}

## Correlated Entities
{% for entity in entities %}
- **{{ entity.name }}** ({{ entity.type }}): {{ entity.description }}
{% endfor %}

## Timeline of Events
{% for event in timeline %}
- **{{ event.time }}**: {{ event.description }} (Source: {{ event.source }}) [^{{ event.citation_id }}]
{% endfor %}

## Citations
{% for citation in citations %}
[^{{ citation.id }}]: {{ citation.file_path }} (Node: {{ citation.node_uuid }})
{% endfor %}
"""


class ReportGenerator:
    """
    Generates JSON and Markdown forensic reports with strict citation linking.
    """

    def __init__(self):
        self.env = Environment(loader=BaseLoader())
        self.template = self.env.from_string(REPORT_TEMPLATE)

    def _validate_citations(self, data: Dict[str, Any]) -> None:
        """
        Enforces that every claim (e.g., event) has a valid citation pointing to an artifact.
        """
        valid_citation_ids = {c["id"] for c in data.get("citations", [])}

        for event in data.get("timeline", []):
            if "citation_id" not in event:
                raise ValueError(f"Missing citation_id for event: {event['description']}")
            if event["citation_id"] not in valid_citation_ids:
                raise ValueError(f"Invalid citation_id '{event['citation_id']}' for event: {event['description']}")

    def generate_json(self, report_data: Dict[str, Any]) -> str:
        """Generates the raw JSON report after validating citations."""
        self._validate_citations(report_data)
        return json.dumps(report_data, indent=2)

    def generate_markdown(self, report_data: Dict[str, Any]) -> str:
        """Generates the formatted Markdown report using Jinja2."""
        self._validate_citations(report_data)
        try:
            return self.template.render(**report_data)
        except Exception as e:
            logger.error(f"Failed to render markdown template: {e}")
            raise e
