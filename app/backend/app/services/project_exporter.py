"""Project Exporter — export project as editable structured file."""
from typing import Dict
from datetime import datetime, timezone


class ProjectExporter:
    """Export project data as structured JSON for archiving and re-import."""

    def export(self, project_data: Dict, format: str = "json") -> Dict:
        """Export project as structured data."""
        return {
            "version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "format": format,
            "project": {
                "name": project_data.get("name", ""),
            },
            "brief": project_data.get("brief", {}),
            "strategy": project_data.get("strategy", {}),
            "assets": project_data.get("assets", []),
            "brand": project_data.get("brand", {}),
        }
