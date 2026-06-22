"""Compliance shim — wraps compliance_checker."""
from app.services.compliance_checker import check_compliance, FORBIDDEN_WORDS, SENSITIVE_PATTERNS


class ComplianceChecker:
    """Wrapper class for backwards compatibility."""

    @staticmethod
    def check(text: str, platform_id: str | None = None) -> dict:
        return check_compliance(text, platform_id)

    @staticmethod
    def check_text(text: str) -> list[dict]:
        """Check a single text string for compliance violations. Returns list of violation dicts."""
        result = check_compliance(text)
        return result.get("violations", [])

    @staticmethod
    def check_brief(brief: dict) -> list[dict]:
        """Check all relevant fields in a brief. Returns list of violation dicts with 'field' key."""
        if not isinstance(brief, dict):
            return []

        violations = []
        text_fields = [
            "product_name", "category", "brand_style",
        ]
        list_fields = [
            "specifications", "selling_points", "materials",
            "target_market", "target_customer", "usage_scenarios",
            "compliance_notes",
        ]

        for field in text_fields:
            value = brief.get(field)
            if isinstance(value, str) and value:
                for v in ComplianceChecker.check_text(value):
                    violations.append({**v, "field": field})

        for field in list_fields:
            values = brief.get(field, [])
            if isinstance(values, list):
                for item in values:
                    text = str(item) if not isinstance(item, (list, dict)) else None
                    if text:
                        for v in ComplianceChecker.check_text(text):
                            violations.append({**v, "field": field})

        return violations
