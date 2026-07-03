from typing import Dict, Optional


class NaturalLanguageQueryParser:
    def parse(self, query: str) -> Dict[str, Optional[str]]:
        text = query.lower()

        filters = {
            "category": None,
            "project_name": None,
            "discipline": None,
            "status": None,
            "author": None
        }

        if "drawing" in text or "drawings" in text:
            filters["category"] = "Drawing"

        if "report" in text or "reports" in text:
            filters["category"] = "Report"

        if "specification" in text or "specifications" in text:
            filters["category"] = "Specification"

        if "structural" in text:
            filters["discipline"] = "Structural"

        if "architectural" in text:
            filters["discipline"] = "Architectural"

        if "mep" in text or "mechanical" in text or "electrical" in text:
            filters["discipline"] = "MEP"

        if "approved" in text:
            filters["status"] = "Approved"

        if "draft" in text:
            filters["status"] = "Draft"

        if "tower a" in text:
            filters["project_name"] = "Tower A"

        if "tower b" in text:
            filters["project_name"] = "Tower B"

        return filters