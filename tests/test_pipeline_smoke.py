"""Smoke tests for pipeline execution modes and CLI entry point."""

import json
from pathlib import Path

from spatial_justice.pipeline import run_pipeline


def test_pipeline_synthetic_execution(tmp_path):
    """Test that synthetic mode executes end-to-end and creates all core deliverables."""
    results = run_pipeline(synthetic=True)

    assert "distance_summary" in results
    assert "accessibility_summary" in results
    assert "correlations" in results
    assert "quintile_disparity" in results

    metrics_file = Path("results/metrics.json")
    findings_file = Path("results/findings.md")

    assert metrics_file.exists()
    assert findings_file.exists()

    with open(metrics_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "metadata" in data
        assert "results" in data
        assert data["results"]["sample_sizes"]["n_analysis_tracts"] == 25

    with open(findings_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Empirical Research Findings" in content
        assert "Adnan Zillur Morshed" in content
