"""Render a stored analysis document as a Markdown report."""


def report_to_markdown(doc: dict) -> str:
    lines = [f"# AChecker report — {doc.get('filename', 'contract')}", ""]

    if doc.get("upload_time"):
        lines.append(f"*Analysed {doc['upload_time']}*")
        lines.append("")
    if doc.get("contract"):
        lines.append(f"**Contract:** `{doc['contract']}`")
        lines.append("")

    lines.append(f"**Result:** {doc.get('summary', 'n/a')}")
    lines.append("")

    findings = doc.get("findings") or []
    for i, finding in enumerate(findings, 1):
        lines.append(f"## {i}. {finding.get('kind', 'Finding')} ({finding.get('severity', '?')})")
        lines.append("")
        lines.append(f"- **Function:** `{finding.get('function', 'unknown')}`")
        if finding.get("intended_behavior"):
            lines.append("- **Note:** flagged as potentially intended behaviour")
        if finding.get("description"):
            lines.append(f"- {finding['description']}")
        if finding.get("instruction"):
            lines.append("")
            lines.append("```")
            lines.append(finding["instruction"])
            lines.append("```")
        for note in finding.get("notes") or []:
            lines.append(f"- {note}")
        lines.append("")

    for block in doc.get("unparsed") or []:
        lines.append(f"## {block.get('title', 'Unparsed output')}")
        lines.append("")
        lines.append("```")
        lines.append(block.get("text", ""))
        lines.append("```")
        lines.append("")

    if not findings and not doc.get("unparsed"):
        lines.append("No access-control issues were reported.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
