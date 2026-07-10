from pathlib import Path

from app.extractors import detect_document_type, extract_metadata, extract_text, normalize_text
from app.models import ComplianceReport, Finding
from app.rules import load_rules


class ComplianceEngine:
    def __init__(self, rules_path):
        self.rules = load_rules(rules_path)

    def review_document(self, file_path):
        path = Path(file_path)

        text = extract_text(path)
        normalized_text = normalize_text(text)
        metadata = extract_metadata(text)

        document_type = detect_document_type(text, self.rules)
        type_rules = self.rules["document_types"].get(document_type, {})

        findings = []

        findings.extend(self._check_required_metadata(metadata, type_rules))
        findings.extend(self._check_mandatory_sections(normalized_text, type_rules))
        findings.extend(self._check_required_terms(normalized_text, type_rules))
        findings.extend(self._check_required_signatures(normalized_text, type_rules))
        findings.extend(self._check_revision_consistency(metadata, normalized_text))

        score = self._calculate_score(findings)

        passed = sum(1 for finding in findings if finding.status == "pass")
        failed = sum(1 for finding in findings if finding.status == "fail")
        warnings = sum(1 for finding in findings if finding.status == "warning")

        return ComplianceReport(
            document_name=path.name,
            detected_document_type=document_type,
            compliance_score=score,
            passed_checks=passed,
            failed_checks=failed,
            warning_checks=warnings,
            findings=findings,
            extracted_metadata=metadata,
        )

    def _check_required_metadata(self, metadata, rules):
        findings = []

        for field in rules.get("required_metadata", []):
            present = bool(metadata.get(field))

            findings.append(
                Finding(
                    rule_id=f"metadata.{field}",
                    title=f"Required metadata: {field}",
                    severity="high",
                    status="pass" if present else "fail",
                    message=f"{field} is present."
                    if present
                    else f"Missing required metadata field: {field}.",
                    evidence=metadata.get(field),
                )
            )

        return findings

    def _check_mandatory_sections(self, text, rules):
        findings = []
        lowered = text.lower()

        for section in rules.get("mandatory_sections", []):
            present = section.lower() in lowered

            findings.append(
                Finding(
                    rule_id=f"section.{section.lower().replace(' ', '_')}",
                    title=f"Mandatory section: {section}",
                    severity="medium",
                    status="pass" if present else "fail",
                    message=f"Section '{section}' is present."
                    if present
                    else f"Missing mandatory section: {section}.",
                )
            )

        return findings

    def _check_required_terms(self, text, rules):
        findings = []
        lowered = text.lower()

        for term in rules.get("required_terms", []):
            present = term.lower() in lowered

            findings.append(
                Finding(
                    rule_id=f"term.{term.lower().replace(' ', '_')}",
                    title=f"Required term: {term}",
                    severity="low",
                    status="pass" if present else "warning",
                    message=f"Required term '{term}' was found."
                    if present
                    else f"Required term '{term}' was not found.",
                )
            )

        return findings

    def _check_required_signatures(self, text, rules):
        findings = []
        lowered = text.lower()

        for role in rules.get("required_signatures", []):
            signature_phrase = f"signature: {role}".lower()
            signed_phrase = f"signed by {role}".lower()

            present = signature_phrase in lowered or signed_phrase in lowered

            findings.append(
                Finding(
                    rule_id=f"signature.{role.lower().replace(' ', '_')}",
                    title=f"Required signature: {role}",
                    severity="high",
                    status="pass" if present else "fail",
                    message=f"Signature for {role} is present."
                    if present
                    else f"Missing required signature for {role}.",
                )
            )

        return findings

    def _check_revision_consistency(self, metadata, text):
        revision = metadata.get("revision")
        has_revision_history = "revision history" in text.lower()

        if not revision:
            return [
                Finding(
                    rule_id="consistency.revision_missing",
                    title="Revision consistency",
                    severity="high",
                    status="fail",
                    message="Revision value is missing, so revision consistency cannot be confirmed.",
                )
            ]

        if not has_revision_history:
            return [
                Finding(
                    rule_id="consistency.revision_history",
                    title="Revision history consistency",
                    severity="medium",
                    status="warning",
                    message="Revision metadata exists, but the document does not include a Revision History section.",
                    evidence=revision,
                )
            ]

        return [
            Finding(
                rule_id="consistency.revision_history",
                title="Revision history consistency",
                severity="medium",
                status="pass",
                message="Revision metadata and Revision History section are both present.",
                evidence=revision,
            )
        ]

    def _calculate_score(self, findings):
        if not findings:
            return 0.0

        weights = {
            "high": 3,
            "medium": 2,
            "low": 1,
        }

        earned = 0
        possible = 0

        for finding in findings:
            weight = weights.get(finding.severity, 1)
            possible += weight

            if finding.status == "pass":
                earned += weight
            elif finding.status == "warning":
                earned += weight * 0.5

        return round((earned / possible) * 100, 2)