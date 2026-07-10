from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Finding:
    rule_id: str
    title: str
    severity: str
    status: str
    message: str
    evidence: str | None = None


@dataclass
class ComplianceReport:
    document_name: str
    detected_document_type: str
    compliance_score: float
    passed_checks: int
    failed_checks: int
    warning_checks: int
    findings: list[Finding] = field(default_factory=list)
    extracted_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["findings"] = [asdict(item) for item in self.findings]
        return data