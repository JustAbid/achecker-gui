"""Parse AChecker's console output into a structured report.

This module is pure (no Flask, no MongoDB) so it can be unit tested on its own.

AChecker prints, for each defect class:

    Checking contract for <Defect-Type>
    ------------------
    <findings for that class>

A "Violated" finding looks like::

    Violated access control check in function transferOwnership(address)
        ( 3642)  e3a:  57  -2 +0 = -2  JUMPI
    +--Attacker can make changes to AC item {0} in function owned()

A "Missing" finding looks like::

    (Non protected SELFDESTRUCT) Missing access control check in function kill()
    Needed to protect following instruction in function kill()
    ( 123)  7b:  ff  -1 +0 = -1  SELFDESTRUCT
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

_SECTION_RE = re.compile(r"Checking contract for\s+(\S+)\s*\n-{3,}\n?")
_CONTRACT_RE = re.compile(r"^Contract (.+?):\s*$", re.MULTILINE)

_VIOLATED_RE = re.compile(r"^Violated access control check in function (.+)$")
_MISSING_RE = re.compile(r"^\((.+?)\) Missing access control check in function (.+)$")
_NEEDED_RE = re.compile(r"^Needed to protect following instruction in function (.+)$")
_NOTE_RE = re.compile(r"^\+--(?:\(Potentially Intended Behavior\)\s*)?(.+)$")
_INSTR_RE = re.compile(r"^\s*\(\s*\d+\)\s+[0-9a-fA-F]+:")

SEVERITY = {
    "Violated access control check": "high",
    "Non protected SELFDESTRUCT": "high",
    "Controlable Address of SELFDESTRUCT": "high",
    "Controlable Target of DELEGATECALL": "high",
    "Missing access control check": "medium",
}

DESCRIPTIONS = {
    "Violated access control check": (
        "An access-control check is present but can be bypassed. An attacker can "
        "influence the storage the check reads — for example by overwriting the "
        "owner slot through an unprotected function — and then pass the check."
    ),
    "Non protected SELFDESTRUCT": (
        "A SELFDESTRUCT is reachable with no owner or authorization check, so anyone "
        "can destroy the contract."
    ),
    "Controlable Address of SELFDESTRUCT": (
        "The beneficiary address of a SELFDESTRUCT is attacker-controllable and is "
        "not guarded by an access-control check."
    ),
    "Controlable Target of DELEGATECALL": (
        "The target of a DELEGATECALL is attacker-controllable with no access-control "
        "guard, which lets arbitrary code run against this contract's storage."
    ),
    "Missing access control check": (
        "A privileged or state-changing operation is reachable with no access-control "
        "check protecting it."
    ),
}


@dataclass
class Finding:
    category: str  # "violated" | "missing"
    kind: str  # human label, one of the SEVERITY keys
    severity: str  # "high" | "medium"
    function: str
    instruction: str = ""
    notes: list = field(default_factory=list)
    intended_behavior: bool = False

    @property
    def description(self) -> str:
        return DESCRIPTIONS.get(self.kind, "")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["description"] = self.description
        return data


@dataclass
class Report:
    contract: str | None = None
    findings: list = field(default_factory=list)
    unparsed: list = field(default_factory=list)  # [{"title": str, "text": str}]
    raw_output: str = ""

    @property
    def issue_count(self) -> int:
        return len(self.findings)

    @property
    def is_clean(self) -> bool:
        return not self.findings and not self.unparsed

    @property
    def severity_counts(self) -> dict:
        counts: dict = {}
        for finding in self.findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts

    def summary(self) -> str:
        if self.is_clean:
            return "No access-control issues found."
        if not self.findings and self.unparsed:
            return "AChecker produced output that could not be parsed (shown below)."
        counts = self.severity_counts
        parts = [f"{counts[s]} {s}" for s in ("high", "medium") if counts.get(s)]
        detail = f" ({', '.join(parts)})" if parts else ""
        noun = "issue" if self.issue_count == 1 else "issues"
        return f"{self.issue_count} access-control {noun} found{detail}."

    def to_dict(self) -> dict:
        return {
            "contract": self.contract,
            "summary": self.summary(),
            "issue_count": self.issue_count,
            "is_clean": self.is_clean,
            "severity_counts": self.severity_counts,
            "findings": [f.to_dict() for f in self.findings],
            "unparsed": self.unparsed,
        }


def parse_report(stdout: str) -> Report:
    """Turn AChecker's stdout into a :class:`Report`."""
    raw = stdout or ""
    text = ANSI_RE.sub("", raw)
    report = Report(raw_output=raw)

    match = _CONTRACT_RE.search(text)
    if match:
        report.contract = match.group(1).strip()

    chunks = _SECTION_RE.split(text)
    if len(chunks) == 1:
        # no recognizable section headers at all
        leftover = text.strip()
        if leftover:
            report.unparsed.append({"title": "AChecker output", "text": leftover})
        return report

    for defect_type, body in zip(chunks[1::2], chunks[2::2]):
        _parse_section(defect_type.strip(), body, report)

    return report


def _parse_section(defect_type: str, body: str, report: Report) -> None:
    current: Finding | None = None
    leftovers: list = []

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or set(stripped) == {"-"}:
            continue
        if stripped.startswith("Checking contract for"):
            break

        violated = _VIOLATED_RE.match(stripped)
        missing = _MISSING_RE.match(stripped)
        needed = _NEEDED_RE.match(stripped)
        note = _NOTE_RE.match(stripped)

        if violated:
            current = Finding(
                category="violated",
                kind="Violated access control check",
                severity="high",
                function=violated.group(1).strip(),
            )
            report.findings.append(current)
        elif missing:
            kind = missing.group(1).strip()
            current = Finding(
                category="missing",
                kind=kind,
                severity=SEVERITY.get(kind, "medium"),
                function=missing.group(2).strip(),
            )
            report.findings.append(current)
        elif current is not None and needed:
            current.notes.append("Unprotected instruction is in function " + needed.group(1).strip())
        elif current is not None and note:
            if "Potentially Intended Behavior" in stripped:
                current.intended_behavior = True
            current.notes.append(note.group(1).strip())
        elif current is not None and _INSTR_RE.match(line):
            if current.instruction:
                current.notes.append(stripped)
            else:
                current.instruction = stripped
        else:
            leftovers.append(line)

    if any(item.strip() for item in leftovers):
        report.unparsed.append(
            {
                "title": f"Checking contract for {defect_type}",
                "text": "\n".join(leftovers).strip(),
            }
        )
