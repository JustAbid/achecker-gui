from achecker_gui.report import Finding, Report, parse_report


def test_empty_output_is_clean():
    report = parse_report("")
    assert report.is_clean
    assert report.issue_count == 0
    assert report.summary() == "No access-control issues found."


def test_clean_contract_fixture(fixture_text):
    report = parse_report(fixture_text("T4.out"))
    assert report.is_clean
    assert report.findings == []
    assert report.unparsed == []


def test_violated_finding_from_cve_fixture(fixture_text):
    report = parse_report(fixture_text("CVE-2021-34273.out"))

    assert report.issue_count == 1
    finding = report.findings[0]
    assert finding.category == "violated"
    assert finding.kind == "Violated access control check"
    assert finding.severity == "high"
    assert finding.function == "transferOwnership(address)"
    assert "JUMPI" in finding.instruction
    assert any("owned()" in note for note in finding.notes)
    assert finding.description
    assert report.summary() == "1 access-control issue found (1 high)."


def test_fallback_function_name_is_preserved(fixture_text):
    report = parse_report(fixture_text("T3.out"))
    assert report.findings[0].function == "() payable"


def test_missing_ac_selfdestruct_and_delegatecall(fixture_text):
    report = parse_report(fixture_text("missing_ac.out"))

    assert report.issue_count == 2
    kinds = {f.kind for f in report.findings}
    assert kinds == {"Non protected SELFDESTRUCT", "Controlable Target of DELEGATECALL"}
    for finding in report.findings:
        assert finding.category == "missing"
        assert finding.severity == "high"
        assert finding.instruction
        assert any("function" in note for note in finding.notes)


def test_solidity_contract_name_and_intended_behavior(fixture_text):
    report = parse_report(fixture_text("solidity_contract.out"))

    assert report.contract == "Wallet"
    assert report.issue_count == 1
    assert report.findings[0].intended_behavior is True


def test_unrecognized_output_goes_to_unparsed(fixture_text):
    report = parse_report(fixture_text("messy.out"))

    assert report.findings == []
    assert report.unparsed
    assert not report.is_clean
    assert "could not be parsed" in report.summary()
    assert "JUMPI" in report.unparsed[0]["text"]


def test_ansi_codes_are_stripped(fixture_text):
    report = parse_report(fixture_text("CVE-2021-34273.out"))
    assert "\x1b[" not in report.findings[0].kind


def test_report_to_dict_shape(fixture_text):
    data = parse_report(fixture_text("CVE-2021-34273.out")).to_dict()
    assert set(data) >= {
        "summary",
        "issue_count",
        "is_clean",
        "severity_counts",
        "findings",
        "unparsed",
        "contract",
    }
    assert data["findings"][0]["description"]


def test_summary_counts_multiple_severities():
    report = Report(
        findings=[
            Finding("violated", "Violated access control check", "high", "a()"),
            Finding("missing", "Missing access control check", "medium", "b()"),
        ]
    )
    assert report.summary() == "2 access-control issues found (1 high, 1 medium)."
