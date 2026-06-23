"""
Canvas version diff service.
"""


class VersionDiff:
    def compare(self, version_a: dict, version_b: dict) -> list:
        changes = []
        all_keys = set(version_a.keys()) | set(version_b.keys())

        for key in all_keys:
            val_a = version_a.get(key)
            val_b = version_b.get(key)

            if val_a != val_b:
                change = {
                    "field": key,
                    "type": "color" if "color" in key else "text",
                    "before": val_a,
                    "after": val_b
                }
                changes.append(change)

        return changes

    def format_for_canvas(self, changes: list) -> dict:
        return {
            "version_a": {},
            "version_b": {},
            "changes": changes
        }
