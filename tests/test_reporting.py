from achecker_gui.report import parse_report
from achecker_gui.reporting import report_to_markdown


def _doc(fixture_text, fixture, filename="c.code"):
    data = parse_report(fixture_text(fixture)).to_dict()
    data["filename"] = filename
    data["upload_time"] = "2026-09-07 10:00:00 AM"
    return data


def test_markdown_for_clean_contract(fixture_text):
    md = report_to_markdown(_doc(fixture_text, "T4.out"))
    assert md.startswith("# AChecker report — c.code")
    assert "No access-control issues were reported." in md


def test_markdown_for_finding_has_function_and_code_block(fixture_text):
    md = report_to_markdown(_doc(fixture_text, "CVE-2021-34273.out"))
    assert "## 1. Violated access control check (high)" in md
    assert "`transferOwnership(address)`" in md
    assert "```" in md
    assert "JUMPI" in md


def test_markdown_includes_unparsed_blocks(fixture_text):
    md = report_to_markdown(_doc(fixture_text, "messy.out"))
    assert "Checking contract for Violated-AC-Check" in md
    assert md.endswith("\n")
